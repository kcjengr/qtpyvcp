"""Reference-only pseudo flow showing integration in existing files.

Not imported by runtime.
"""


def datasource_init_flow(inifile):
    """Pseudo steps for linuxcnc_datasource.py"""
    # 1) owners_cfg = resolve_owners(inifile)
    # 2) self._axis_motion_owner = owners_cfg.owners
    # 3) self._ownership_signature = make_signature(self._axis_motion_owner, ("X","Y","Z","A","B","C"))
    # 4) log signature and source
    pass


def vtk_backplot_runtime_flow(axis_owners, switchkins_type):
    """Pseudo steps for vtk_backplot.py"""
    # 1) policy = derive_policy(axis_owners, switchkins_type)
    # 2) choose breadcrumb frame from policy
    # 3) choose table-aware linear feedback path from policy
    # 4) keep actor and path transforms consistent with policy
    pass


def vtk_canon_load_flow(axis_owners, switchkins_type):
    """Pseudo steps for vtk_canon.py"""
    # 1) policy = derive_policy(axis_owners, switchkins_type)
    # 2) if policy.enable_table_rotary_sampling: sample table rotary path points
    # 3) else: keep standard segment insertion
    pass
