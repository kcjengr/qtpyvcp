#!/usr/bin/env python3
"""Fake-LinuxCNC harness: drives tool_db_backend over stdin/stdout (tooldb v2.1).

Proves the Phase 1 gate behaviors without a running LinuxCNC:
  1. version handshake
  2. 'g' serves full lines including D I J Q and remark
  3. 'p' (touch-off push) updates the DB
  4. GUI-side add/delete (second connection) visible at next 'g' w/o restart
  5. 'l'/'u' maintain in_use
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "harness_tools.db")
QTPYVCP_SRC = os.path.abspath(os.path.join(HERE, "..", "src"))
LCNC_PY = os.environ.get("LINUXCNC_PYTHON", os.path.expanduser("~/dev/linuxcnc/lib/python"))
PY = sys.executable

if os.path.exists(DB):
    os.remove(DB)
for suffix in ("-wal", "-shm"):
    if os.path.exists(DB + suffix):
        os.remove(DB + suffix)

sys.path.insert(0, QTPYVCP_SRC)
from qtpyvcp.lib.db_tool.base import Session, Base, configure_database, get_engine
from qtpyvcp.lib.db_tool.tool_table import Tool, ToolTable

# ---- seed two lathe tools (GUI-process role) ----
configure_database(DB)
Base.metadata.create_all(get_engine())
s = Session()
s.add(ToolTable(id=1, name="Harness Tool Table"))
s.flush()
s.add(Tool(tool_no=2, pocket=-1, x_offset=0.0, z_offset=0.0,
           y_offset=0, a_offset=0, b_offset=0, c_offset=0,
           u_offset=0, v_offset=0, w_offset=0,
           diameter=0.03125, i_offset=85.0, j_offset=5.0, q_offset=2,
           in_use=0, remark="SCLCR-CCGT-21.51-RH TURNING TOOL", tool_table_id=1))
s.add(Tool(tool_no=20, pocket=-1, x_offset=0.0, z_offset=0.0,
           y_offset=0, a_offset=0, b_offset=0, c_offset=0,
           u_offset=0, v_offset=0, w_offset=0,
           diameter=0.4531, i_offset=0.0, j_offset=0.0, q_offset=9,
           in_use=0, remark="29/64 DRILL", tool_table_id=1))
s.commit()

# ---- spawn the backend exactly as LinuxCNC would ----
env = dict(os.environ, PYTHONPATH=QTPYVCP_SRC + ":" + LCNC_PY)
proc = subprocess.Popen(
    [PY, os.path.join(QTPYVCP_SRC, "qtpyvcp/tools/tool_db_backend.py"), DB, "debug"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    env=env, text=True, bufsize=1)

failures = []

def expect(desc, cond):
    print(("PASS  " if cond else "FAIL  ") + desc)
    if not cond:
        failures.append(desc)

def send(line):
    proc.stdin.write(line + "\n")
    proc.stdin.flush()

def read_until_fini():
    lines = []
    while True:
        line = proc.stdout.readline().rstrip("\n")
        if not line:
            break
        if line.startswith("FINI") or line.startswith("NAK"):
            lines.append(line)
            return lines
        lines.append(line)
    return lines

# 1. handshake
ack = proc.stdout.readline().strip()
expect("handshake replies v2.1 (got %r)" % ack, ack == "v2.1")

# 2. initial get — full lathe lines
send("g")
lines = read_until_fini()
tool_lines = [l for l in lines if l.startswith("T")]
expect("g returns 2 tools + FINI", len(tool_lines) == 2 and lines[-1].startswith("FINI"))
t2 = next((l for l in tool_lines if l.startswith("T2 ")), "")
expect("T2 line carries I/J/Q (got %r)" % t2,
       "I85" in t2 and "J5" in t2 and "Q2" in t2)
expect("T2 line carries D and remark",
       "D0.03125" in t2 and ";SCLCR-CCGT-21.51-RH" in t2)

# 3. touch-off push (p) updates DB
send("p T2 P-1 X0.123456 Z-0.05 D0.03125 I85 J5 Q2")
reply = proc.stdout.readline().strip()
expect("p acknowledged with FINI (got %r)" % reply, reply.startswith("FINI"))
check = Session()
x_now = check.query(Tool).filter(Tool.tool_no == 2).one().x_offset
check.close()
expect("touch-off X persisted to DB (%r)" % x_now, abs(x_now - 0.123456) < 1e-9)

# 4. GUI adds + deletes tools while backend is running (no restart)
gui = Session()
gui.add(Tool(tool_no=55, pocket=-1, x_offset=0, y_offset=0, z_offset=0,
             a_offset=0, b_offset=0, c_offset=0, u_offset=0, v_offset=0,
             w_offset=0, diameter=0.02, i_offset=87.0, j_offset=3.0,
             q_offset=3, in_use=0, remark="ADDED LIVE", tool_table_id=1))
gui.query(Tool).filter(Tool.tool_no == 20).delete()
gui.commit()
gui.close()

send("g")
lines = read_until_fini()
tool_lines = [l for l in lines if l.startswith("T")]
nums = sorted(int(l.split()[0][1:]) for l in tool_lines)
expect("live add/delete visible at next g (tools now %s)" % nums, nums == [2, 55])

# 5. spindle load / unload maintain in_use
send("l T2 P0")
proc.stdout.readline()
check = Session()
in_use = check.query(Tool).filter(Tool.tool_no == 2).one().in_use
check.close()
expect("l T2 sets in_use=1", in_use == 1)

send("u T0 P0")
proc.stdout.readline()
check = Session()
any_in_use = check.query(Tool).filter(Tool.in_use == 1).count()
check.close()
expect("u T0 clears in_use", any_in_use == 0)

# 6. unknown command NAKs but does not kill the backend
send("zz")
reply = proc.stdout.readline().strip()
expect("unknown cmd NAKs (got %r)" % reply, reply.startswith("NAK"))
send("g")
lines = read_until_fini()
expect("backend still alive after NAK", lines and lines[-1].startswith("FINI"))

proc.stdin.close()
proc.wait(timeout=5)
print("\nbackend stderr (tail):")
print("\n".join(proc.stderr.read().splitlines()[-6:]))
print("\n%s" % ("ALL CHECKS PASSED" if not failures else "FAILURES: %s" % failures))
sys.exit(1 if failures else 0)
