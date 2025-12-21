from pyrevit import script
from pyrevit.loader import sessionmgr
from pyrevit.loader import sessioninfo

logger = script.get_logger()
results = script.get_results()

# re-load pyrevit session.
sessionmgr.reload_pyrevit()

results.newsession = sessioninfo.get_session_uuid()
