from run_clusterv_web import app
from werkzeug.middleware.dispatcher import DispatcherMiddleware

application = DispatcherMiddleware(
    None,
    {'/ClusterVW': app}
)
