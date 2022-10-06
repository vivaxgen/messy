
from rhombus.lib.utils import cerr, set_dbhandler_class, get_dbhandler_class
from rhombus.routes import add_route_view, add_route_view_class

from messy.views.menunav import get_menunav
from messy.ext.ngsmgr.models.handler import generate_handler_class
from messy.ext.ngsmgr.models.schema import FastqUploadJob
from messy.ext.ngsmgr import configkeys as ck


set_dbhandler_class(generate_handler_class(get_dbhandler_class()))
get_menunav().add_after('Plate', ('NGSRun', 'url:/ngsrun'))


def includeme(config):

    settings = config.get_settings()
    FastqUploadJob.set_root_storage_path(settings[ck.rb_attachment_root])

    add_route_view_class(
        config, 'messy.ext.ngsmgr.views.ngsrun.NGSRunViewer', 'messy-ngsmgr.ngsrun',
        '/ngsrun',
        '/ngsrun/@@action',
        '/ngsrun/@@plateaction',
        '/ngsrun/@@add',
        ('/ngsrun/@@lookup', 'lookup', 'json'),
        '/ngsrun/{id}@@edit',
        '/ngsrun/{id}@@save',
        ('/ngsrun/{id}@@attachment/{fieldname}', 'attachment'),
        ('/ngsrun/{id}', 'view')
    )

    add_route_view_class(
        config, 'messy.ext.ngsmgr.views.panel.PanelViewer', 'messy-ngsmgr.panel',
        '/panel',
        '/panel/@@add',
        ('/panel/{id}', 'view'),
    )

    add_route_view_class(
        config, 'messy.ext.ngsmgr.views.fastqpair.FastqPairViewer', 'messy-ngsmgr.fastqpair',
        '/fastqpair',
        '/fastqpair/@@action',
        '/fastqpair/@@add',
        # '/fastqpair/@@uploadmgr',
        ('/fastqpair/@@upload/{sesskey}', 'upload'),
        '/fastqpair/{sesskey}@@target',     # upload target for both read-1 and read-2
        '/fastqpair/{id}@@edit',
        '/fastqpair/{id}@@save',
        ('/fastqpair/{id}', 'view'),
    )

    # id here is a session key, generated based on user_id and ngsrun_id that holds the
    # fastq
    add_route_view_class(
        config, 'messy.ext.ngsmgr.views.uploadjob.FastqUploadJobViewer',
        'messy-ngsmgr.uploadjob.fastq',
        '/uploadjob/fastq',
        '/uploadjob/fastq/@@action',
        '/uploadjob/fastq/@@add',
        '/uploadjob/fastq/{id}@@status',
        '/uploadjob/fastq/{id}@@save',
        ('/uploadjob/fastq/{id}@@target'),
        ('/uploadjob/fastq/{id}', 'view'),

    )


# EOF
