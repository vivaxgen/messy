
from rhombus.lib import rpc

# public functions

def list_institituions(request, token):

    userinstance, errmsg = get_userinstance_by_token(request, token)

def pipeline_upload(request, token, run_code, sample_code, data):

    userinstance, errmsg = get_userinstance_by_token(request, token)
    if userinstance is None:
        return {'auth': False, 'user': None, 'errmsg': errmsg}

    dbh = get_dbhandler()

    # parse incoming request
    # https://github.com/trmznt/ncov19-pipeline sends the following dictionary

    # either get the Sequence or create a new Sequence

    try:
        sq = dbh.get_sequences(
            groups=None,
            specs=[{'run_code': run_code, 'sample_code': sample_code}],
            user=userinstance,
            raise_if_empty=True
        )

    except dbh.NoResultFound:
        sq = dbh.Sequence(
            sequencingrun=run_code,
            sample=sample_code
        )
        dbh.session().add(sq)

    sq.update(data)

# EOF
