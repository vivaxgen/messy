
from pyramid_rpc.jsonrpc import JsonRpcError

from rhombus.lib.utils import get_dbhandler
from rhombus.lib import rpc


# public method

def list_institutions(request, token):

    user, errmsg = rpc.get_userinstance_by_token(request, token)

    dbh = get_dbhandler()
    institutions = dbh.get_institutions()
    return {'institutions': institutions}


def data_status(request, token):

    user, errmsg = rpc.get_userinstance_by_token(request, token)

    dbh = get_dbhandler()
    dbsess = dbh.session()

    d = {
        'total_collections': dbh.Collection.query(dbsess).count(),
        'total_samples': dbh.Collection.query(dbsess).count(),
    }

    return d

# EOF
