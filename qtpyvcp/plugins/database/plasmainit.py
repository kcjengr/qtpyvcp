#!/usr/bin/python
import os
import sqlite3

try:
    os.remove('plasma.db')
except OSError:
    pass

db = sqlite3.connect('plasma.db')
print("Opened database successfully")

cursor = db.cursor()
#
# Create table MACHINE
#
cursor.execute('''
    CREATE TABLE machine(ma_id INTEGER PRIMARY KEY, ma_name TEXT, ma_serviceheight REAL )
''')
db.commit()
m_name = 'Hypertherm 45XP'
m_serviceheight = 45.0

cursor.execute('''INSERT INTO machine(ma_name, ma_serviceheight)
                  VALUES(?,?)''', (m_name, m_serviceheight))
pl_name = "Hypertherm 65"
cursor.execute('''INSERT INTO machine(ma_name, ma_serviceheight)
                  VALUES(?,?)''', (m_name, m_serviceheight))

cursor = db.execute("SELECT ma_id, ma_name, ma_serviceheight FROM machine")
for row in cursor:
    print("MA_ID = ", row[0])
    print("MA_NAME = ", row[1])
    print("MA_SERVICEHEIGHT = ", row[2], "\n")

#
# Create table MEASURE
#
cursor.execute('''
    CREATE TABLE measure(me_id INTEGER PRIMARY KEY, me_name TEXT, me_units_per_in REAL )
''')
db.commit()
m_name = 'Metric'
m_units = 25.4
cursor.execute('''INSERT INTO measure(me_name, me_units_per_in)
                  VALUES(?,?)''', (m_name, m_units))

m_name = 'Imperial'
m_units = 1.0
cursor.execute('''INSERT INTO measure(me_name, me_units_per_in)
                  VALUES(?,?)''', (m_name, m_units))
cursor = db.execute("SELECT me_id, me_name, me_units_per_in FROM measure")
for row in cursor:
    print("ME_ID = ", row[0])
    print("ME_NAME = ", row[1])
    print("ME_UNITS_PER_IN = ", row[2], "\n")

#
# Create table MEASURE
#
cursor.execute('''
    CREATE TABLE gas(ga_id INTEGER PRIMARY KEY, ga_name TEXT,ga_spare TEXT )
''')
m_name = "Air"
m_spare = ""
cursor.execute('''INSERT INTO gas(ga_name,ga_spare)
                  VALUES(?,?)''', (m_name, m_spare))
m_name = "Argon"
cursor.execute('''INSERT INTO gas(ga_name,ga_spare)
                  VALUES(?,?)''', (m_name, m_spare))
m_name = "F5"
cursor.execute('''INSERT INTO gas(ga_name, ga_spare)
                  VALUES(?,?)''', (m_name, m_spare))

cursor = db.execute("SELECT ga_id, ga_name FROM gas")
for row in cursor:
    print("GA_ID = ", row[0])
    print("GA_NAME = ", row[1], "\n")

#
# Create table Operation
#
cursor.execute('''
    CREATE TABLE operation(op_id INTEGER PRIMARY KEY, op_name TEXT,op_spare TEXT )
''')
m_name = "Cut"
m_spare = ""
cursor.execute('''INSERT INTO operation(op_name,op_spare)
                  VALUES(?,?)''', (m_name, m_spare))
m_name = "Mark"
cursor.execute('''INSERT INTO operation(op_name,op_spare)
                  VALUES(?,?)''', (m_name, m_spare))
m_name = "Gouge"
cursor.execute('''INSERT INTO operation(op_name, op_spare)
                  VALUES(?,?)''', (m_name, m_spare))

cursor = db.execute("SELECT op_id, op_name FROM operation")
for row in cursor:
    print("OP_ID = ", row[0])
    print("OP_NAME = ", row[1], "\n")

#
# Create table material
#

cursor.execute('''
    CREATE TABLE material(mt_id INTEGER PRIMARY KEY, mt_name TEXT,mt_spare TEXT )
''')
m_name = "Mild Steel"
m_spare = ""
cursor.execute('''INSERT INTO material(mt_name,mt_spare)
                  VALUES(?,?)''', (m_name, m_spare))
m_name = "Stainless Steel"
cursor.execute('''INSERT INTO material(mt_name,mt_spare)
                  VALUES(?,?)''', (m_name, m_spare))
m_name = "Aluminiumn"
cursor.execute('''INSERT INTO material(mt_name, mt_spare)
                  VALUES(?,?)''', (m_name, m_spare))

cursor = db.execute("SELECT mt_id, mt_name FROM material")
for row in cursor:
    print("MT_ID = ", row[0])
    print("MT_NAME = ", row[1], "\n")

#
# Create table consumable
#

cursor.execute('''
    CREATE TABLE consumable(co_id INTEGER PRIMARY KEY, co_ma_id INTEGER, co_name TEXT, co_image_path TEXT )
''')
m_machine = 1
m_name = "Shielded"
m_path = ".\\shielded45.jpg"
cursor.execute('''INSERT INTO consumable(co_ma_id, co_name, co_image_path)
                  VALUES(?,?,?)''', (m_machine, m_name, m_path))
m_name = "Unshielded"
m_path = ".\\unshielded45.jpg"
cursor.execute('''INSERT INTO consumable(co_ma_id, co_name,co_image_path)
                  VALUES(?,?,?)''', (m_machine, m_name, m_path))
m_name = "Finecut"
m_path = ".\\finecut45.jpg"
cursor.execute('''INSERT INTO consumable(co_ma_id, co_name,co_image_path)
                  VALUES(?,?,?)''', (m_machine, m_name, m_path))
m_machine = 2
m_name = "Shielded"
m_path = ".\\shielded65.jpg"
cursor.execute('''INSERT INTO consumable(co_ma_id, co_name, co_image_path)
                  VALUES(?,?,?)''', (m_machine, m_name, m_path))
m_name = "Unshielded"
m_path = ".\\unshielded65.jpg"
cursor.execute('''INSERT INTO consumable(co_ma_id, co_name,co_image_path)
                  VALUES(?,?,?)''', (m_machine, m_name, m_path))
m_name = "Finecut"
m_path = ".\\finecut65.jpg"
cursor.execute('''INSERT INTO consumable(co_ma_id, co_name,co_image_path)
                  VALUES(?,?,?)''', (m_machine, m_name, m_path))

cursor = db.execute("SELECT co_id, co_ma_id, co_name, co_image_path FROM consumable")
for row in cursor:
    print("CO_ID = ", row[0])
    print("CO_MA_ID = ", row[1])
    print("CO_NAME = ", row[2])
    print("CO_IMAGE_PATH = ", row[3], "\n")

#
# Create table quality
#

cursor.execute('''
    CREATE TABLE quality(qu_id INTEGER PRIMARY KEY, qu_name TEXT,qu_spare TEXT )
''')
m_name = "Best Quality"
m_spare = ""
cursor.execute('''INSERT INTO quality(qu_name,qu_spare)
                  VALUES(?,?)''', (m_name, m_spare))
m_name = "Production Quality"
cursor.execute('''INSERT INTO quality(qu_name,qu_spare)
                  VALUES(?,?)''', (m_name, m_spare))

cursor = db.execute("SELECT qu_id, qu_name FROM quality")
for row in cursor:
    print("MT_ID = ", row[0])
    print("MT_NAME = ", row[1], "\n")

#
# Create table leadin
#

cursor.execute('''
    CREATE TABLE leadin(le_id INTEGER PRIMARY KEY, le_name TEXT,le_spare TEXT )
''')
m_name = "Normal"
m_spare = ""
cursor.execute('''INSERT INTO leadin(le_name,le_spare)
                  VALUES(?,?)''', (m_name, m_spare))
m_name = "Ramp"
cursor.execute('''INSERT INTO leadin(le_name,le_spare)
                  VALUES(?,?)''', (m_name, m_spare))
m_name = "Wiggle"
cursor.execute('''INSERT INTO leadin(le_name, le_spare)
                  VALUES(?,?)''', (m_name, m_spare))
m_name = "Puddle Jump"
cursor.execute('''INSERT INTO leadin(le_name, le_spare)
                  VALUES(?,?)''', (m_name, m_spare))

cursor = db.execute("SELECT le_id, le_name FROM leadin")
for row in cursor:
    print("LE_ID = ", row[0])
    print("LE_NAME = ", row[1], "\n")

#
# Create table thickness
#
cursor.execute('''
    CREATE TABLE thickness(th_id INTEGER PRIMARY KEY, th_mt_id INTEGER, th_name TEXT, th_thickness REAL )
''')
m_th_id = 1  # metric
m_name = "0.6mm"
m_thickness = "0.6"
cursor.execute('''INSERT INTO thickness(th_mt_id, th_name,th_thickness)
                  VALUES(?,?,?)''', (m_th_id, m_name, m_thickness))
m_name = "0.5mm"
m_thickness = "0.6"
cursor.execute('''INSERT INTO thickness(th_mt_id, th_name,th_thickness)
                  VALUES(?,?,?)''', (m_th_id, m_name, m_thickness))

m_name = "0.8mm"
m_thickness = "0.8"
cursor.execute('''INSERT INTO thickness(th_mt_id, th_name,th_thickness)
                  VALUES(?,?,?)''', (m_th_id, m_name, m_thickness))
m_name = "1.0mm"
m_thickness = "1.0"
cursor.execute('''INSERT INTO thickness(th_mt_id, th_name,th_thickness)
                  VALUES(?,?,?)''', (m_th_id, m_name, m_thickness))
m_name = "1.5mm"
m_thickness = "1.5"
cursor.execute('''INSERT INTO thickness(th_mt_id, th_name,th_thickness)
                  VALUES(?,?,?)''', (m_th_id, m_name, m_thickness))
m_name = "2mm"
m_thickness = "2.0"
cursor.execute('''INSERT INTO thickness(th_mt_id, th_name,th_thickness)
                  VALUES(?,?,?)''', (m_th_id, m_name, m_thickness))
m_name = "3mm"
m_thickness = "3.0"
cursor.execute('''INSERT INTO thickness(th_mt_id, th_name,th_thickness)
                  VALUES(?,?,?)''', (m_th_id, m_name, m_thickness))

m_name = "4mm"
m_thickness = "4.0"
cursor.execute('''INSERT INTO thickness(th_mt_id, th_name,th_thickness)
                  VALUES(?,?,?)''', (m_th_id, m_name, m_thickness))
m_name = "6mm"
m_thickness = "6.0"
cursor.execute('''INSERT INTO thickness(th_mt_id, th_name,th_thickness)
                  VALUES(?,?,?)''', (m_th_id, m_name, m_thickness))
m_name = "8mm"
m_thickness = "8.0"
cursor.execute('''INSERT INTO thickness(th_mt_id, th_name,th_thickness)
                  VALUES(?,?,?)''', (m_th_id, m_name, m_thickness))
m_name = "10mm"
m_thickness = "10.0"
cursor.execute('''INSERT INTO thickness(th_mt_id, th_name,th_thickness)
                  VALUES(?,?,?)''', (m_th_id, m_name, m_thickness))
m_name = "12mm"
m_thickness = "12.0"
cursor.execute('''INSERT INTO thickness(th_mt_id, th_name,th_thickness)
                  VALUES(?,?,?)''', (m_th_id, m_name, m_thickness))

m_name = "16mm"
m_thickness = "16.0"
cursor.execute('''INSERT INTO thickness(th_mt_id, th_name,th_thickness)
                  VALUES(?,?,?)''', (m_th_id, m_name, m_thickness))
m_name = "20mm"
m_thickness = "20.0"
cursor.execute('''INSERT INTO thickness(th_mt_id, th_name,th_thickness)
                  VALUES(?,?,?)''', (m_th_id, m_name, m_thickness))
m_name = "25mm"
m_thickness = "25.0"
cursor.execute('''INSERT INTO thickness(th_mt_id, th_name,th_thickness)
                  VALUES(?,?,?)''', (m_th_id, m_name, m_thickness))
m_name = "32mm"
m_thickness = "32.0"
cursor.execute('''INSERT INTO thickness(th_mt_id, th_name,th_thickness)
                  VALUES(?,?,?)''', (m_th_id, m_name, m_thickness))

cursor = db.execute("SELECT th_id, th_mt_id, th_name, th_thickness FROM thickness")
for row in cursor:
    print("TH_ID = ", row[0])
    print("TH_MT_ID = ", row[1])
    print("TH_NAME = ", row[2])
    print("TH_THICKNESS = ", row[3], "\n")

#
# Create table cutchart FINALLY!!
#

cursor.execute('''
    CREATE TABLE cutchart(cu_id INTEGER PRIMARY KEY, cu_me_id INTEGER, cu_ma_id INTEGER, cu_co_id INTEGER, cu_mt_id INTEGER, cu_th_id INTEGER, cu_op_id INTEGER, cu_ga_id INTEGER,
                          cu_qu_id INTEGER, cu_pierce_ht REAL, cu_pierce_delay REAL, cu_cut_ht REAL, cu_cut_spd REAL, cu_volts REAL, cu_kerf_width REAL,
                          cu_thc_delay REAL, cu_plunge_rate REAL, cu_puddle_ht REAL,  cu_amps REAL, cu_pressure REAL)
''')

# 2 mm
m_ma_id = 1  # Machine:       Hypertherm 45XP
m_me_id = 1  # Measurement:   Metric
m_co_id = 1  # Consumable:    Shielded
m_mt_id = 1  # Material:      Mild Steel
m_th_id = 6  # Thickness:     2mm
m_op_id = 1  # Operation:     Cut
m_ga_id = 1  # GAS:           Air
m_qu_id = 1  # Quality        Best Quality
m_pierce_ht = 3.8  # Pierce Height (mm)
m_pierce_dly = 0.2  # Pierce Delay (mm)
m_cut_ht = 1.5  # Cut height (mm)
m_cut_spd = 5560  # Cutting speed (mm/min)
m_volts = 128  # Cutting Volts
m_kerf_width = 1.4  # Kerf Width (mm)
m_thc_delay = 0.5  # Thc Delay (seconds)
m_plung_rate = 0.0  # Plunge rate (whats wrong with G0? - This is macine dependent and should not be in cut chart)
m_puddle_ht = 7.6  # Height to raise above puddle when piercing. Have no idea how high this should be (say 200% pierce height)
m_amps = 45  # Amps to cut at
m_pressure = 0.0  # Gas Pressure (psi) - 0.0 = Automatic mode

cursor.execute('''INSERT INTO cutchart (cu_ma_id,cu_me_id, cu_co_id, cu_mt_id, cu_th_id, cu_op_id, cu_ga_id, cu_qu_id, cu_pierce_ht, cu_pierce_delay, cu_cut_ht, 
                                        cu_cut_spd, cu_volts, cu_kerf_width, cu_thc_delay, cu_plunge_rate, cu_puddle_ht, cu_amps, cu_pressure)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
               (m_ma_id, m_me_id, m_co_id, m_mt_id, m_th_id, m_op_id, m_ga_id, m_qu_id,
                m_pierce_ht, m_pierce_dly, m_cut_ht, m_cut_spd, m_volts, m_kerf_width, m_thc_delay, m_plung_rate,
                m_puddle_ht, m_amps, m_pressure))

m_qu_id = 2  # Quality        Production  Quality
m_volts = 125  # Cutting Volts
m_cut_spd = 7910  # Cutting speed (mm/min)
cursor.execute('''INSERT INTO cutchart (cu_ma_id, cu_me_id, cu_co_id, cu_mt_id, cu_th_id, cu_op_id, cu_ga_id, cu_qu_id, cu_pierce_ht, cu_pierce_delay, cu_cut_ht, 
                                        cu_cut_spd, cu_volts, cu_kerf_width, cu_thc_delay, cu_plunge_rate, cu_puddle_ht, cu_amps, cu_pressure)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
               (m_ma_id, m_me_id, m_co_id, m_mt_id, m_th_id, m_op_id, m_ga_id, m_qu_id,
                m_pierce_ht, m_pierce_dly, m_cut_ht, m_cut_spd, m_volts, m_kerf_width, m_thc_delay, m_plung_rate,
                m_puddle_ht, m_amps, m_pressure))

# 3 mm               
m_ma_id = 1  # Machine:       Hypertherm 45XP
m_co_id = 1  # Consumable:    Shielded
m_mt_id = 1  # Material:      Mild Steel
m_th_id = 7  # Thickness:     3mm
m_op_id = 1  # Operation:     Cut
m_ga_id = 1  # GAS:           Air
m_qu_id = 1  # Quality        Best Quality
m_pierce_ht = 3.8  # Pierce Height (mm)
m_pierce_dly = 0.2  # Pierce Delay (mm)
m_cut_ht = 1.5  # Cut height (mm)
m_cut_spd = 3960  # Cutting speed (mm/min)
m_volts = 128  # Cutting Volts
m_kerf_width = 1.4  # Kerf Width (mm)
m_thc_delay = 0.5  # Thc Delay (seconds)
m_plung_rate = 0.0  # Plunge rate (whats wrong with G0? - This is macine dependent and should not be in cut chart)
m_puddle_ht = 7.6  # Height to raise above puddle when piercing. Have no idea how high this should be (say 200% pierce height)
m_amps = 45  # Amps to cut at
m_pressure = 0.0  # Gas Pressure (psi) - 0.0 = Automatic mode
cursor.execute('''INSERT INTO cutchart (cu_ma_id, cu_me_id, cu_co_id, cu_mt_id, cu_th_id, cu_op_id, cu_ga_id, cu_qu_id, cu_pierce_ht, cu_pierce_delay, cu_cut_ht, 
                                        cu_cut_spd, cu_volts, cu_kerf_width, cu_thc_delay, cu_plunge_rate, cu_puddle_ht, cu_amps, cu_pressure)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
               (m_ma_id, m_me_id, m_co_id, m_mt_id, m_th_id, m_op_id, m_ga_id, m_qu_id,
                m_pierce_ht, m_pierce_dly, m_cut_ht, m_cut_spd, m_volts, m_kerf_width, m_thc_delay, m_plung_rate,
                m_puddle_ht, m_amps, m_pressure))

m_qu_id = 2  # Quality        Production  Quality
m_cut_spd = 5590  # Cutting speed (mm/min)

cursor.execute('''INSERT INTO cutchart (cu_ma_id, cu_me_id, cu_co_id, cu_mt_id, cu_th_id, cu_op_id, cu_ga_id, cu_qu_id, cu_pierce_ht, cu_pierce_delay, cu_cut_ht, 
                                        cu_cut_spd, cu_volts, cu_kerf_width, cu_thc_delay, cu_plunge_rate, cu_puddle_ht, cu_amps, cu_pressure)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
               (m_ma_id, m_me_id, m_co_id, m_mt_id, m_th_id, m_op_id, m_ga_id, m_qu_id,
                m_pierce_ht, m_pierce_dly, m_cut_ht, m_cut_spd, m_volts, m_kerf_width, m_thc_delay, m_plung_rate,
                m_puddle_ht, m_amps, m_pressure))

# 4 mm                         

m_ma_id = 1  # Machine:       Hypertherm 45XP
m_co_id = 1  # Consumable:    Shielded
m_mt_id = 1  # Material:      Mild Steel
m_th_id = 8  # Thickness:     3mm
m_op_id = 1  # Operation:     Cut
m_ga_id = 1  # GAS:           Air
m_qu_id = 1  # Quality        Best Quality
m_pierce_ht = 3.8  # Pierce Height (mm)
m_pierce_dly = 0.4  # Pierce Delay (mm)
m_cut_ht = 1.5  # Cut height (mm)
m_cut_spd = 2800  # Cutting speed (mm/min)
m_volts = 128  # Cutting Volts
m_kerf_width = 1.4  # Kerf Width (mm)
m_thc_delay = 0.5  # Thc Delay (seconds)
m_plung_rate = 0.0  # Plunge rate (whats wrong with G0? - This is macine dependent and should not be in cut chart)
m_puddle_ht = 7.6  # Height to raise above puddle when piercing. Have no idea how high this should be (say 200% pierce height)
m_amps = 45  # Amps to cut at
m_pressure = 0.0  # Gas Pressure (psi) - 0.0 = Automatic mode
cursor.execute('''INSERT INTO cutchart (cu_ma_id, cu_me_id, cu_co_id, cu_mt_id, cu_th_id, cu_op_id, cu_ga_id, cu_qu_id, cu_pierce_ht, cu_pierce_delay, cu_cut_ht, 
                                        cu_cut_spd, cu_volts, cu_kerf_width, cu_thc_delay, cu_plunge_rate, cu_puddle_ht, cu_amps, cu_pressure)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
               (m_ma_id, m_me_id, m_co_id, m_mt_id, m_th_id, m_op_id, m_ga_id, m_qu_id,
                m_pierce_ht, m_pierce_dly, m_cut_ht, m_cut_spd, m_volts, m_kerf_width, m_thc_delay, m_plung_rate,
                m_puddle_ht, m_amps, m_pressure))

m_qu_id = 2  # Quality        Production  Quality
m_cut_spd = 3960  # Cutting speed (mm/min)

cursor.execute('''INSERT INTO cutchart (cu_ma_id, cu_me_id, cu_co_id, cu_mt_id, cu_th_id, cu_op_id, cu_ga_id, cu_qu_id, cu_pierce_ht, cu_pierce_delay, cu_cut_ht, 
                                        cu_cut_spd, cu_volts, cu_kerf_width, cu_thc_delay, cu_plunge_rate, cu_puddle_ht, cu_amps, cu_pressure)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
               (m_ma_id, m_me_id, m_co_id, m_mt_id, m_th_id, m_op_id, m_ga_id, m_qu_id,
                m_pierce_ht, m_pierce_dly, m_cut_ht, m_cut_spd, m_volts, m_kerf_width, m_thc_delay, m_plung_rate,
                m_puddle_ht, m_amps, m_pressure))

# 6 mm

m_ma_id = 1  # Machine:       Hypertherm 45XP
m_co_id = 1  # Consumable:    Shielded
m_mt_id = 1  # Material:      Mild Steel
m_th_id = 9  # Thickness:     3mm
m_op_id = 1  # Operation:     Cut
m_ga_id = 1  # GAS:           Air
m_qu_id = 1  # Quality        Best Quality
m_pierce_ht = 3.8  # Pierce Height (mm)
m_pierce_dly = 0.6  # Pierce Delay (mm)
m_cut_ht = 1.5  # Cut height (mm)
m_cut_spd = 1430  # Cutting speed (mm/min)
m_volts = 130  # Cutting Volts
m_kerf_width = 1.5  # Kerf Width (mm)
m_thc_delay = 0.5  # Thc Delay (seconds)
m_plung_rate = 0.0  # Plunge rate (whats wrong with G0? - This is macine dependent and should not be in cut chart)
m_puddle_ht = 7.6  # Height to raise above puddle when piercing. Have no idea how high this should be (say 200% pierce height)
m_amps = 45  # Amps to cut at
m_pressure = 0.0  # Gas Pressure (psi) - 0.0 = Automatic mode
cursor.execute('''INSERT INTO cutchart (cu_ma_id, cu_me_id, cu_co_id, cu_mt_id, cu_th_id, cu_op_id, cu_ga_id, cu_qu_id, cu_pierce_ht, cu_pierce_delay, cu_cut_ht, 
                                        cu_cut_spd, cu_volts, cu_kerf_width, cu_thc_delay, cu_plunge_rate, cu_puddle_ht, cu_amps, cu_pressure)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
               (m_ma_id, m_me_id, m_co_id, m_mt_id, m_th_id, m_op_id, m_ga_id, m_qu_id,
                m_pierce_ht, m_pierce_dly, m_cut_ht, m_cut_spd, m_volts, m_kerf_width, m_thc_delay, m_plung_rate,
                m_puddle_ht, m_amps, m_pressure))

m_qu_id = 2  # Quality        Production  Quality
m_cut_spd = 2110  # Cutting speed (mm/min)

cursor.execute('''INSERT INTO cutchart (cu_ma_id,  cu_me_id, cu_co_id, cu_mt_id, cu_th_id, cu_op_id, cu_ga_id, cu_qu_id, cu_pierce_ht, cu_pierce_delay, cu_cut_ht, 
                                        cu_cut_spd, cu_volts, cu_kerf_width, cu_thc_delay, cu_plunge_rate, cu_puddle_ht, cu_amps, cu_pressure)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
               (m_ma_id, m_me_id, m_co_id, m_mt_id, m_th_id, m_op_id, m_ga_id, m_qu_id,
                m_pierce_ht, m_pierce_dly, m_cut_ht, m_cut_spd, m_volts, m_kerf_width, m_thc_delay, m_plung_rate,
                m_puddle_ht, m_amps, m_pressure))
# 8mm

m_ma_id = 1  # Machine:       Hypertherm 45XP
m_co_id = 1  # Consumable:    Shielded
m_mt_id = 1  # Material:      Mild Steel
m_th_id = 10  # Thickness:     3mm
m_op_id = 1  # Operation:     Cut
m_ga_id = 1  # GAS:           Air
m_qu_id = 1  # Quality        Best Quality
m_pierce_ht = 3.8  # Pierce Height (mm)
m_pierce_dly = 0.6  # Pierce Delay (mm)
m_cut_ht = 1.7  # Cut height (mm)
m_cut_spd = 1020  # Cutting speed (mm/min)
m_volts = 133  # Cutting Volts
m_kerf_width = 1.4  # Kerf Width (mm)
m_thc_delay = 0.5  # Thc Delay (seconds)
m_plung_rate = 0.0  # Plunge rate (whats wrong with G0? - This is macine dependent and should not be in cut chart)
m_puddle_ht = 7.6  # Height to raise above puddle when piercing. Have no idea how high this should be (say 200% pierce height)
m_amps = 45  # Amps to cut at
m_pressure = 0.0  # Gas Pressure (psi) - 0.0 = Automatic mode
cursor.execute('''INSERT INTO cutchart (cu_ma_id, cu_me_id, cu_co_id, cu_mt_id, cu_th_id, cu_op_id, cu_ga_id, cu_qu_id, cu_pierce_ht, cu_pierce_delay, cu_cut_ht, 
                                        cu_cut_spd, cu_volts, cu_kerf_width, cu_thc_delay, cu_plunge_rate, cu_puddle_ht, cu_amps, cu_pressure)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
               (m_ma_id, m_me_id, m_co_id, m_mt_id, m_th_id, m_op_id, m_ga_id, m_qu_id,
                m_pierce_ht, m_pierce_dly, m_cut_ht, m_cut_spd, m_volts, m_kerf_width, m_thc_delay, m_plung_rate,
                m_puddle_ht, m_amps, m_pressure))

m_qu_id = 2  # Quality        Production  Quality
m_cut_spd = 1385  # Cutting speed (mm/min)
m_volts = 130  # Cutting Volts

cursor.execute('''INSERT INTO cutchart (cu_ma_id,  cu_me_id, cu_co_id, cu_mt_id, cu_th_id, cu_op_id, cu_ga_id, cu_qu_id, cu_pierce_ht, cu_pierce_delay, cu_cut_ht, 
                                        cu_cut_spd, cu_volts, cu_kerf_width, cu_thc_delay, cu_plunge_rate, cu_puddle_ht, cu_amps, cu_pressure)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
               (m_ma_id, m_me_id, m_co_id, m_mt_id, m_th_id, m_op_id, m_ga_id, m_qu_id,
                m_pierce_ht, m_pierce_dly, m_cut_ht, m_cut_spd, m_volts, m_kerf_width, m_thc_delay, m_plung_rate,
                m_puddle_ht, m_amps, m_pressure))

# 10mm

m_ma_id = 1  # Machine:       Hypertherm 45XP
m_co_id = 1  # Consumable:    Shielded
m_mt_id = 1  # Material:      Mild Steel
m_th_id = 11  # Thickness:     3mm
m_op_id = 1  # Operation:     Cut
m_ga_id = 1  # GAS:           Air
m_qu_id = 1  # Quality        Best Quality
m_pierce_ht = 3.8  # Pierce Height (mm)
m_pierce_dly = 0.8  # Pierce Delay (mm)
m_cut_ht = 1.5  # Cut height (mm)
m_cut_spd = 780  # Cutting speed (mm/min)
m_volts = 136  # Cutting Volts
m_kerf_width = 1.8  # Kerf Width (mm)
m_thc_delay = 0.5  # Thc Delay (seconds)
m_plung_rate = 0.0  # Plunge rate (whats wrong with G0? - This is macine dependent and should not be in cut chart)
m_puddle_ht = 7.6  # Height to raise above puddle when piercing. Have no idea how high this should be (say 200% pierce height)
m_amps = 45  # Amps to cut at
m_pressure = 0.0  # Gas Pressure (psi) - 0.0 = Automatic mode
cursor.execute('''INSERT INTO cutchart (cu_ma_id, cu_me_id,  cu_co_id, cu_mt_id, cu_th_id, cu_op_id, cu_ga_id, cu_qu_id, cu_pierce_ht, cu_pierce_delay, cu_cut_ht, 
                                        cu_cut_spd, cu_volts, cu_kerf_width, cu_thc_delay, cu_plunge_rate, cu_puddle_ht, cu_amps, cu_pressure)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
               (m_ma_id, m_me_id, m_co_id, m_mt_id, m_th_id, m_op_id, m_ga_id, m_qu_id,
                m_pierce_ht, m_pierce_dly, m_cut_ht, m_cut_spd, m_volts, m_kerf_width, m_thc_delay, m_plung_rate,
                m_puddle_ht, m_amps, m_pressure))

m_qu_id = 2  # Quality        Production  Quality
m_cut_spd = 920  # Cutting speed (mm/min)
m_volts = 134  # Cutting Volts

cursor.execute('''INSERT INTO cutchart (cu_ma_id, cu_me_id,  cu_co_id, cu_mt_id, cu_th_id, cu_op_id, cu_ga_id, cu_qu_id, cu_pierce_ht, cu_pierce_delay, cu_cut_ht, 
                                        cu_cut_spd, cu_volts, cu_kerf_width, cu_thc_delay, cu_plunge_rate, cu_puddle_ht, cu_amps, cu_pressure)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
               (m_ma_id, m_me_id, m_co_id, m_mt_id, m_th_id, m_op_id, m_ga_id, m_qu_id,
                m_pierce_ht, m_pierce_dly, m_cut_ht, m_cut_spd, m_volts, m_kerf_width, m_thc_delay, m_plung_rate,
                m_puddle_ht, m_amps, m_pressure))

# 12mm

m_ma_id = 1  # Machine:       Hypertherm 45XP
m_co_id = 1  # Consumable:    Shielded
m_mt_id = 1  # Material:      Mild Steel
m_th_id = 12  # Thickness:     3mm
m_op_id = 1  # Operation:     Cut
m_ga_id = 1  # GAS:           Air
m_qu_id = 1  # Quality        Best Quality
m_pierce_ht = 3.8  # Pierce Height (mm)
m_pierce_dly = 1.0  # Pierce Delay (mm)
m_cut_ht = 1.5  # Cut height (mm)
m_cut_spd = 780  # Cutting speed (mm/min)
m_volts = 140  # Cutting Volts
m_kerf_width = 1.9  # Kerf Width (mm)
m_thc_delay = 0.5  # Thc Delay (seconds)
m_plung_rate = 0.0  # Plunge rate (whats wrong with G0? - This is macine dependent and should not be in cut chart)
m_puddle_ht = 7.6  # Height to raise above puddle when piercing. Have no idea how high this should be (say 200% pierce height)
m_amps = 45  # Amps to cut at
m_pressure = 0.0  # Gas Pressure (psi) - 0.0 = Automatic mode
cursor.execute('''INSERT INTO cutchart (cu_ma_id, cu_me_id, cu_co_id, cu_mt_id, cu_th_id, cu_op_id, cu_ga_id, cu_qu_id, cu_pierce_ht, cu_pierce_delay, cu_cut_ht, 
                                        cu_cut_spd, cu_volts, cu_kerf_width, cu_thc_delay, cu_plunge_rate, cu_puddle_ht, cu_amps, cu_pressure)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
               (m_ma_id, m_me_id, m_co_id, m_mt_id, m_th_id, m_op_id, m_ga_id, m_qu_id,
                m_pierce_ht, m_pierce_dly, m_cut_ht, m_cut_spd, m_volts, m_kerf_width, m_thc_delay, m_plung_rate,
                m_puddle_ht, m_amps, m_pressure))

m_qu_id = 2  # Quality        Production  Quality
m_cut_spd = 920  # Cutting speed (mm/min)
m_volts = 138  # Cutting Volts

cursor.execute('''INSERT INTO cutchart (cu_ma_id, cu_me_id, cu_co_id, cu_mt_id, cu_th_id, cu_op_id, cu_ga_id, cu_qu_id, cu_pierce_ht, cu_pierce_delay, cu_cut_ht, 
                                        cu_cut_spd, cu_volts, cu_kerf_width, cu_thc_delay, cu_plunge_rate, cu_puddle_ht, cu_amps, cu_pressure)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
               (m_ma_id, m_me_id, m_co_id, m_mt_id, m_th_id, m_op_id, m_ga_id, m_qu_id,
                m_pierce_ht, m_pierce_dly, m_cut_ht, m_cut_spd, m_volts, m_kerf_width, m_thc_delay, m_plung_rate,
                m_puddle_ht, m_amps, m_pressure))

# 16mm

m_ma_id = 1  # Machine:       Hypertherm 45XP
m_co_id = 1  # Consumable:    Shielded
m_mt_id = 1  # Material:      Mild Steel
m_th_id = 13  # Thickness:     3mm
m_op_id = 1  # Operation:     Cut
m_ga_id = 1  # GAS:           Air
m_qu_id = 1  # Quality        Best Quality
m_pierce_ht = 0  # Pierce Height (mm)
m_pierce_dly = 0  # Pierce Delay (mm)
m_cut_ht = 1.5  # Cut height (mm)
m_cut_spd = 310  # Cutting speed (mm/min)
m_volts = 146  # Cutting Volts
m_kerf_width = 2.1  # Kerf Width (mm)
m_thc_delay = 0.5  # Thc Delay (seconds)
m_plung_rate = 0.0  # Plunge rate (whats wrong with G0? - This is macine dependent and should not be in cut chart)
m_puddle_ht = 7.6  # Height to raise above puddle when piercing. Have no idea how high this should be (say 200% pierce height)
m_amps = 45  # Amps to cut at
m_pressure = 0.0  # Gas Pressure (psi) - 0.0 = Automatic mode
cursor.execute('''INSERT INTO cutchart (cu_ma_id,  cu_me_id, cu_co_id, cu_mt_id, cu_th_id, cu_op_id, cu_ga_id, cu_qu_id, cu_pierce_ht, cu_pierce_delay, cu_cut_ht, 
                                        cu_cut_spd, cu_volts, cu_kerf_width, cu_thc_delay, cu_plunge_rate, cu_puddle_ht, cu_amps, cu_pressure)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
               (m_ma_id, m_me_id, m_co_id, m_mt_id, m_th_id, m_op_id, m_ga_id, m_qu_id,
                m_pierce_ht, m_pierce_dly, m_cut_ht, m_cut_spd, m_volts, m_kerf_width, m_thc_delay, m_plung_rate,
                m_puddle_ht, m_amps, m_pressure))

m_qu_id = 2  # Quality        Production  Quality
m_cut_spd = 400  # Cutting speed (mm/min)
m_volts = 141  # Cutting Volts

cursor.execute('''INSERT INTO cutchart (cu_ma_id, cu_me_id, cu_co_id, cu_mt_id, cu_th_id, cu_op_id, cu_ga_id, cu_qu_id, cu_pierce_ht, cu_pierce_delay, cu_cut_ht, 
                                        cu_cut_spd, cu_volts, cu_kerf_width, cu_thc_delay, cu_plunge_rate, cu_puddle_ht, cu_amps, cu_pressure)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
               (m_ma_id, m_me_id, m_co_id, m_mt_id, m_th_id, m_op_id, m_ga_id, m_qu_id,
                m_pierce_ht, m_pierce_dly, m_cut_ht, m_cut_spd, m_volts, m_kerf_width, m_thc_delay, m_plung_rate,
                m_puddle_ht, m_amps, m_pressure))

# 20mm 

m_ma_id = 1  # Machine:       Hypertherm 45XP
m_co_id = 1  # Consumable:    Shielded
m_mt_id = 1  # Material:      Mild Steel
m_th_id = 14  # Thickness:     3mm
m_op_id = 1  # Operation:     Cut
m_ga_id = 1  # GAS:           Air
m_qu_id = 1  # Quality        Best Quality
m_pierce_ht = 0  # Pierce Height (mm)
m_pierce_dly = 0  # Pierce Delay (mm)
m_cut_ht = 1.5  # Cut height (mm)
m_cut_spd = 170  # Cutting speed (mm/min)
m_volts = 152  # Cutting Volts
m_kerf_width = 2.3  # Kerf Width (mm)
m_thc_delay = 0.5  # Thc Delay (seconds)
m_plung_rate = 0.0  # Plunge rate (whats wrong with G0? - This is macine dependent and should not be in cut chart)
m_puddle_ht = 7.6  # Height to raise above puddle when piercing. Have no idea how high this should be (say 200% pierce height)
m_amps = 45  # Amps to cut at
m_pressure = 0.0  # Gas Pressure (psi) - 0.0 = Automatic mode
cursor.execute('''INSERT INTO cutchart (cu_ma_id, cu_me_id, cu_co_id, cu_mt_id, cu_th_id, cu_op_id, cu_ga_id, cu_qu_id, cu_pierce_ht, cu_pierce_delay, cu_cut_ht, 
                                        cu_cut_spd, cu_volts, cu_kerf_width, cu_thc_delay, cu_plunge_rate, cu_puddle_ht, cu_amps, cu_pressure)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
               (m_ma_id, m_me_id, m_co_id, m_mt_id, m_th_id, m_op_id, m_ga_id, m_qu_id,
                m_pierce_ht, m_pierce_dly, m_cut_ht, m_cut_spd, m_volts, m_kerf_width, m_thc_delay, m_plung_rate,
                m_puddle_ht, m_amps, m_pressure))

m_qu_id = 2  # Quality        Production  Quality
m_cut_spd = 240  # Cutting speed (mm/min)
m_volts = 147  # Cutting Volts

cursor.execute('''INSERT INTO cutchart (cu_ma_id, cu_me_id, cu_co_id, cu_mt_id, cu_th_id, cu_op_id, cu_ga_id, cu_qu_id, cu_pierce_ht, cu_pierce_delay, cu_cut_ht, 
                                        cu_cut_spd, cu_volts, cu_kerf_width, cu_thc_delay, cu_plunge_rate, cu_puddle_ht, cu_amps, cu_pressure)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
               (m_ma_id, m_me_id, m_co_id, m_mt_id, m_th_id, m_op_id, m_ga_id, m_qu_id,
                m_pierce_ht, m_pierce_dly, m_cut_ht, m_cut_spd, m_volts, m_kerf_width, m_thc_delay, m_plung_rate,
                m_puddle_ht, m_amps, m_pressure))

# 25mm 

m_ma_id = 1  # Machine:       Hypertherm 45XP
m_co_id = 1  # Consumable:    Shielded
m_mt_id = 1  # Material:      Mild Steel
m_th_id = 15  # Thickness:     3mm
m_op_id = 1  # Operation:     Cut
m_ga_id = 1  # GAS:           Air
m_qu_id = 1  # Quality        Best Quality
m_pierce_ht = 0  # Pierce Height (mm)
m_pierce_dly = 0  # Pierce Delay (mm)
m_cut_ht = 1.5  # Cut height (mm)
m_cut_spd = 110  # Cutting speed (mm/min)
m_volts = 157  # Cutting Volts
m_kerf_width = 3.0  # Kerf Width (mm)
m_thc_delay = 0.5  # Thc Delay (seconds)
m_plung_rate = 0.0  # Plunge rate (whats wrong with G0? - This is macine dependent and should not be in cut chart)
m_puddle_ht = 7.6  # Height to raise above puddle when piercing. Have no idea how high this should be (say 200% pierce height)
m_amps = 45  # Amps to cut at
m_pressure = 0.0  # Gas Pressure (psi) - 0.0 = Automatic mode
cursor.execute('''INSERT INTO cutchart (cu_ma_id, cu_me_id, cu_co_id, cu_mt_id, cu_th_id, cu_op_id, cu_ga_id, cu_qu_id, cu_pierce_ht, cu_pierce_delay, cu_cut_ht, 
                                        cu_cut_spd, cu_volts, cu_kerf_width, cu_thc_delay, cu_plunge_rate, cu_puddle_ht, cu_amps, cu_pressure)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
               (m_ma_id, m_me_id, m_co_id, m_mt_id, m_th_id, m_op_id, m_ga_id, m_qu_id,
                m_pierce_ht, m_pierce_dly, m_cut_ht, m_cut_spd, m_volts, m_kerf_width, m_thc_delay, m_plung_rate,
                m_puddle_ht, m_amps, m_pressure))

m_qu_id = 2  # Quality        Production  Quality
m_cut_spd = 145  # Cutting speed (mm/min)
m_volts = 157  # Cutting Volts

cursor.execute('''INSERT INTO cutchart (cu_ma_id, cu_me_id, cu_co_id, cu_mt_id, cu_th_id, cu_op_id, cu_ga_id, cu_qu_id, cu_pierce_ht, cu_pierce_delay, cu_cut_ht, 
                                        cu_cut_spd, cu_volts, cu_kerf_width, cu_thc_delay, cu_plunge_rate, cu_puddle_ht, cu_amps, cu_pressure)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
               (m_ma_id, m_me_id, m_co_id, m_mt_id, m_th_id, m_op_id, m_ga_id, m_qu_id,
                m_pierce_ht, m_pierce_dly, m_cut_ht, m_cut_spd, m_volts, m_kerf_width, m_thc_delay, m_plung_rate,
                m_puddle_ht, m_amps, m_pressure))

cursor = db.execute("SELECT cu_id, cu_ma_id, cu_co_id, cu_mt_id, cu_th_id, cu_op_id, cu_ga_id, cu_qu_id, cu_pierce_ht, cu_pierce_delay,\
                     cu_cut_ht, cu_cut_spd, cu_volts, cu_kerf_width, cu_thc_delay, cu_plunge_rate, cu_puddle_ht, cu_amps, cu_pressure, cu_me_id  FROM cutchart")
for row in cursor:
    print("CU_ID = ", row[0])
    print("CU_MA_ID = ", row[1])
    print("CU_ME_ID = ", row[19])
    print("CU_CO_ID = ", row[2])
    print("CU_MT_ID = ", row[3])
    print("CU_TH_ID = ", row[4])
    print("CU_OP_ID = ", row[5])
    print("CU_GA_ID = ", row[6])
    print("CU_QU_ID = ", row[7])
    print("CU_PIERCE_HT = ", row[8])
    print("CU_PIERCE_DELAY = ", row[9])
    print("CU_CUT_HT = ", row[10])
    print("CU_CUT_SPD = ", row[11])
    print("CU_VOLTS = ", row[12])
    print("CU_KERF_WIDTH = ", row[13])
    print("CU_THC_DELAY = ", row[14])
    print("CU_PLUNGE_RATE = ", row[15])
    print("CU_PUDDLE_HT = ", row[16])
    print("CU_AMPS = ", row[17])
    print("CU_PRESSURE = ", row[18], "\n")

print("Operation done successfully")
db.commit()
db.close()
