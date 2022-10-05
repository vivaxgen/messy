
from messy.views.sample import SampleViewer
from messy.ext.ngsmgr.views.fastqpair import generate_fastqpair_table


def extend_viewers():
    extend_sample_viewer()


def extend_sample_viewer():

    SampleViewer.tab_contents.insert(
        0,
        ('fastqpairs', 'FastQ Files', generate_fastqpair_table_sample)
    )


# generate fastqpair for SampleViewer
def generate_fastqpair_table_sample(viewer, html_anchor=None):

    return generate_fastqpair_table(
        viewer.obj.fastqpairs,
        viewer.request,
        viewer.can_modify(),
        additional_fields=['panel', 'ngsrun']
    )


extend_viewers()

# EOF
