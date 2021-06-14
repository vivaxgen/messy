"""Initial tables

Revision ID: 1aa13fb0e4f3
Revises: 
Create Date: 2021-06-12 12:38:21.611753

"""
from alembic import op
import sqlalchemy as sa
import rhombus.models.core


# revision identifiers, used by Alembic.
revision = '1aa13fb0e4f3'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('groups',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=32), nullable=False),
    sa.Column('desc', sa.String(length=128), server_default='', nullable=False),
    sa.Column('scheme', rhombus.models.core.YAMLCol(length=256), server_default='', nullable=False),
    sa.Column('flags', sa.Integer(), server_default='0', nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_groups')),
    sa.UniqueConstraint('name', name=op.f('uq_groups_name'))
    )
    op.create_table('syslogs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('stamp', sa.TIMESTAMP(), nullable=False),
    sa.Column('level', sa.SmallInteger(), nullable=True),
    sa.Column('msg', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_syslogs'))
    )
    op.create_table('sysregs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('key', sa.String(length=64), nullable=False),
    sa.Column('bindata', sa.LargeBinary(), nullable=False),
    sa.Column('mimetype', sa.String(length=32), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_sysregs')),
    sa.UniqueConstraint('key', name=op.f('uq_sysregs_key'))
    )
    op.create_table('userclasses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('domain', sa.String(length=16), nullable=False),
    sa.Column('desc', sa.String(length=64), server_default='', nullable=False),
    sa.Column('referer', sa.String(length=128), server_default='', nullable=False),
    sa.Column('autoadd', sa.Boolean(), nullable=False),
    sa.Column('credscheme', rhombus.models.core.YAMLCol(length=256), nullable=False),
    sa.Column('flags', sa.Integer(), server_default='0', nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_userclasses')),
    sa.UniqueConstraint('domain', name=op.f('uq_userclasses_domain'))
    )
    op.create_table('associated_groups',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('group_id', sa.Integer(), nullable=False),
    sa.Column('assoc_group_id', sa.Integer(), nullable=False),
    sa.Column('role', sa.String(length=1), server_default='R', nullable=False),
    sa.ForeignKeyConstraint(['assoc_group_id'], ['groups.id'], name=op.f('fk_associated_groups_assoc_group_id_groups')),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], name=op.f('fk_associated_groups_group_id_groups')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_associated_groups')),
    sa.UniqueConstraint('group_id', 'assoc_group_id', name=op.f('uq_associated_groups_group_id_assoc_group_id'))
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('login', sa.String(length=32), nullable=False),
    sa.Column('credential', sa.String(length=128), nullable=False),
    sa.Column('lastlogin', sa.TIMESTAMP(), nullable=True),
    sa.Column('userclass_id', sa.Integer(), nullable=False),
    sa.Column('lastname', sa.String(length=32), nullable=False),
    sa.Column('firstname', sa.String(length=32), server_default='', nullable=False),
    sa.Column('email', sa.String(length=32), nullable=False),
    sa.Column('email2', sa.String(length=64), server_default='', nullable=False),
    sa.Column('institution', sa.String(length=64), server_default='', nullable=False),
    sa.Column('address', sa.String(length=128), server_default='', nullable=False),
    sa.Column('contact', sa.String(length=64), server_default='', nullable=False),
    sa.Column('status', sa.String(length=1), server_default='A', nullable=False),
    sa.Column('flags', sa.Integer(), server_default='0', nullable=False),
    sa.Column('primarygroup_id', sa.Integer(), nullable=False),
    sa.Column('yaml', rhombus.models.core.YAMLCol(), nullable=True),
    sa.ForeignKeyConstraint(['primarygroup_id'], ['groups.id'], name=op.f('fk_users_primarygroup_id_groups')),
    sa.ForeignKeyConstraint(['userclass_id'], ['userclasses.id'], name=op.f('fk_users_userclass_id_userclasses')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
    sa.UniqueConstraint('email', name=op.f('uq_users_email')),
    sa.UniqueConstraint('login', 'userclass_id', name=op.f('uq_users_login_userclass_id')),
    sa.UniqueConstraint('login', name=op.f('uq_users_login'))
    )
    op.create_index(op.f('ix_users_email2'), 'users', ['email2'], unique=False)
    op.create_index(op.f('ix_users_lastname'), 'users', ['lastname'], unique=False)
    op.create_index(op.f('ix_users_primarygroup_id'), 'users', ['primarygroup_id'], unique=False)
    op.create_index(op.f('ix_users_userclass_id'), 'users', ['userclass_id'], unique=False)
    op.create_table('collections',
    sa.Column('code', sa.String(length=16), nullable=False),
    sa.Column('description', sa.String(length=256), server_default='', nullable=False),
    sa.Column('remark', sa.String(length=2048), server_default='', nullable=False),
    sa.Column('data', sa.JSON(), server_default='null', nullable=False),
    sa.Column('group_id', sa.Integer(), nullable=False),
    sa.Column('contact', sa.String(length=64), server_default='', nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lastuser_id', sa.Integer(), nullable=True),
    sa.Column('stamp', sa.TIMESTAMP(), nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], name=op.f('fk_collections_group_id_groups')),
    sa.ForeignKeyConstraint(['lastuser_id'], ['users.id'], name=op.f('fk_collections_lastuser_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_collections')),
    sa.UniqueConstraint('code', name=op.f('uq_collections_code'))
    )
    op.create_table('datalogs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('stamp', sa.TIMESTAMP(), nullable=False),
    sa.Column('class_id', sa.SmallInteger(), nullable=False),
    sa.Column('object_id', sa.Integer(), nullable=False),
    sa.Column('action_id', sa.SmallInteger(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_datalogs_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_datalogs'))
    )
    op.create_table('eks',
    sa.Column('key', sa.String(length=128), nullable=False),
    sa.Column('desc', sa.String(length=128), nullable=False),
    sa.Column('data', sa.LargeBinary(), nullable=True),
    sa.Column('syskey', sa.Boolean(), nullable=False),
    sa.Column('member_of_id', sa.Integer(), nullable=True),
    sa.Column('group_id', sa.Integer(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lastuser_id', sa.Integer(), nullable=True),
    sa.Column('stamp', sa.TIMESTAMP(), nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], name=op.f('fk_eks_group_id_groups')),
    sa.ForeignKeyConstraint(['lastuser_id'], ['users.id'], name=op.f('fk_eks_lastuser_id_users')),
    sa.ForeignKeyConstraint(['member_of_id'], ['eks.id'], name=op.f('fk_eks_member_of_id_eks')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_eks')),
    sa.UniqueConstraint('key', 'member_of_id', name=op.f('uq_eks_key_member_of_id'))
    )
    op.create_index(op.f('ix_eks_member_of_id'), 'eks', ['member_of_id'], unique=False)
    op.create_table('institutions',
    sa.Column('code', sa.String(length=24), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('address', sa.String(length=128), server_default='', nullable=False),
    sa.Column('zipcode', sa.String(length=8), server_default='', nullable=False),
    sa.Column('contact', sa.String(length=64), server_default='', nullable=False),
    sa.Column('remark', sa.String(length=2048), server_default='', nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lastuser_id', sa.Integer(), nullable=True),
    sa.Column('stamp', sa.TIMESTAMP(), nullable=False),
    sa.ForeignKeyConstraint(['lastuser_id'], ['users.id'], name=op.f('fk_institutions_lastuser_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_institutions')),
    sa.UniqueConstraint('code', name=op.f('uq_institutions_code')),
    sa.UniqueConstraint('name', name=op.f('uq_institutions_name'))
    )
    op.create_table('users_groups',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('group_id', sa.Integer(), nullable=False),
    sa.Column('role', sa.String(length=1), server_default='M', nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], name=op.f('fk_users_groups_group_id_groups')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_users_groups_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users_groups')),
    sa.UniqueConstraint('user_id', 'group_id', name=op.f('uq_users_groups_user_id_group_id'))
    )
    op.create_table('actionlogs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('action_id', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=1), server_default='P', nullable=True),
    sa.Column('objs', sa.String(length=128), server_default='', nullable=False),
    sa.Column('stamp', sa.TIMESTAMP(), nullable=False),
    sa.ForeignKeyConstraint(['action_id'], ['eks.id'], name=op.f('fk_actionlogs_action_id_eks')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_actionlogs_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_actionlogs'))
    )
    op.create_table('collection_institution',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('collection_id', sa.Integer(), nullable=False),
    sa.Column('institution_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['collection_id'], ['collections.id'], name=op.f('fk_collection_institution_collection_id_collections')),
    sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], name=op.f('fk_collection_institution_institution_id_institutions')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_collection_institution')),
    sa.UniqueConstraint('collection_id', 'institution_id', name=op.f('uq_collection_institution_collection_id_institution_id'))
    )
    op.create_table('files',
    sa.Column('path', sa.String(length=128), nullable=False),
    sa.Column('type_id', sa.Integer(), nullable=False),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.Column('mimetype_id', sa.Integer(), nullable=False),
    sa.Column('group_id', sa.Integer(), nullable=False),
    sa.Column('bindata', sa.LargeBinary(), server_default='', nullable=False),
    sa.Column('permanent', sa.Boolean(), nullable=False),
    sa.Column('flags', sa.Integer(), server_default='0', nullable=False),
    sa.Column('acl', sa.Integer(), server_default='0', nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lastuser_id', sa.Integer(), nullable=True),
    sa.Column('stamp', sa.TIMESTAMP(), nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], name=op.f('fk_files_group_id_groups')),
    sa.ForeignKeyConstraint(['lastuser_id'], ['users.id'], name=op.f('fk_files_lastuser_id_users')),
    sa.ForeignKeyConstraint(['mimetype_id'], ['eks.id'], name=op.f('fk_files_mimetype_id_eks')),
    sa.ForeignKeyConstraint(['parent_id'], ['files.id'], name=op.f('fk_files_parent_id_files')),
    sa.ForeignKeyConstraint(['type_id'], ['eks.id'], name=op.f('fk_files_type_id_eks')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_files')),
    sa.UniqueConstraint('path', name=op.f('uq_files_path'))
    )
    op.create_index(op.f('ix_files_parent_id'), 'files', ['parent_id'], unique=False)
    op.create_table('groups_roles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('group_id', sa.Integer(), nullable=False),
    sa.Column('role_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], name=op.f('fk_groups_roles_group_id_groups')),
    sa.ForeignKeyConstraint(['role_id'], ['eks.id'], name=op.f('fk_groups_roles_role_id_eks')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_groups_roles')),
    sa.UniqueConstraint('group_id', 'role_id', name=op.f('uq_groups_roles_group_id_role_id'))
    )
    op.create_table('plates',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('group_id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=32), server_default='', nullable=False),
    sa.Column('specimen_type_id', sa.Integer(), nullable=False),
    sa.Column('experiment_type_id', sa.Integer(), nullable=False),
    sa.Column('remark', sa.Text(), server_default='', nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lastuser_id', sa.Integer(), nullable=True),
    sa.Column('stamp', sa.TIMESTAMP(), nullable=False),
    sa.ForeignKeyConstraint(['experiment_type_id'], ['eks.id'], name=op.f('fk_plates_experiment_type_id_eks')),
    sa.ForeignKeyConstraint(['group_id'], ['groups.id'], name=op.f('fk_plates_group_id_groups')),
    sa.ForeignKeyConstraint(['lastuser_id'], ['users.id'], name=op.f('fk_plates_lastuser_id_users')),
    sa.ForeignKeyConstraint(['specimen_type_id'], ['eks.id'], name=op.f('fk_plates_specimen_type_id_eks')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_plates_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_plates')),
    sa.UniqueConstraint('code', name=op.f('uq_plates_code'))
    )
    op.create_table('samples',
    sa.Column('collection_id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=16), server_default='', nullable=False),
    sa.Column('lab_code', sa.String(length=16), server_default='', nullable=False),
    sa.Column('received_date', sa.Date(), nullable=False),
    sa.Column('sequence_name', sa.String(length=64), server_default='', nullable=False),
    sa.Column('species_id', sa.Integer(), nullable=False),
    sa.Column('passage_id', sa.Integer(), server_default='0', nullable=False),
    sa.Column('collection_date', sa.Date(), nullable=False),
    sa.Column('location', sa.String(length=64), server_default='', nullable=False),
    sa.Column('location_info', sa.String(length=128), server_default='', nullable=False),
    sa.Column('host_id', sa.Integer(), nullable=False),
    sa.Column('host_info', sa.String(length=64), server_default='', nullable=False),
    sa.Column('host_gender', sa.String(length=1), server_default='X', nullable=False),
    sa.Column('host_age', sa.Float(), server_default='0', nullable=False),
    sa.Column('host_occupation_id', sa.Integer(), nullable=False),
    sa.Column('host_status_id', sa.Integer(), nullable=False),
    sa.Column('host_severity', sa.Integer(), server_default='-1', nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=False),
    sa.Column('specimen_type_id', sa.Integer(), nullable=False),
    sa.Column('outbreak', sa.String(), server_default='', nullable=False),
    sa.Column('last_vaccinated_date', sa.Date(), nullable=True),
    sa.Column('last_vaccinated_info', sa.String(), server_default='', nullable=False),
    sa.Column('treatment', sa.String(length=64), server_default='', nullable=False),
    sa.Column('viral_load', sa.Float(), server_default='-1', nullable=False),
    sa.Column('ct_value', sa.Float(), server_default='-1', nullable=False),
    sa.Column('ct_method_id', sa.Integer(), nullable=False),
    sa.Column('originating_code', sa.String(length=32), nullable=True),
    sa.Column('originating_institution_id', sa.Integer(), nullable=False),
    sa.Column('sampling_code', sa.String(length=32), nullable=True),
    sa.Column('sampling_institution_id', sa.Integer(), nullable=False),
    sa.Column('related_sample_id', sa.Integer(), nullable=True),
    sa.Column('remark', sa.Text(), server_default='', nullable=False),
    sa.Column('extdata', sa.JSON(), server_default='null', nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lastuser_id', sa.Integer(), nullable=True),
    sa.Column('stamp', sa.TIMESTAMP(), nullable=False),
    sa.ForeignKeyConstraint(['category_id'], ['eks.id'], name=op.f('fk_samples_category_id_eks')),
    sa.ForeignKeyConstraint(['collection_id'], ['collections.id'], name=op.f('fk_samples_collection_id_collections'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['ct_method_id'], ['eks.id'], name=op.f('fk_samples_ct_method_id_eks')),
    sa.ForeignKeyConstraint(['host_id'], ['eks.id'], name=op.f('fk_samples_host_id_eks')),
    sa.ForeignKeyConstraint(['host_occupation_id'], ['eks.id'], name=op.f('fk_samples_host_occupation_id_eks')),
    sa.ForeignKeyConstraint(['host_status_id'], ['eks.id'], name=op.f('fk_samples_host_status_id_eks')),
    sa.ForeignKeyConstraint(['lastuser_id'], ['users.id'], name=op.f('fk_samples_lastuser_id_users')),
    sa.ForeignKeyConstraint(['originating_institution_id'], ['institutions.id'], name=op.f('fk_samples_originating_institution_id_institutions')),
    sa.ForeignKeyConstraint(['related_sample_id'], ['samples.id'], name=op.f('fk_samples_related_sample_id_samples')),
    sa.ForeignKeyConstraint(['sampling_institution_id'], ['institutions.id'], name=op.f('fk_samples_sampling_institution_id_institutions')),
    sa.ForeignKeyConstraint(['species_id'], ['eks.id'], name=op.f('fk_samples_species_id_eks')),
    sa.ForeignKeyConstraint(['specimen_type_id'], ['eks.id'], name=op.f('fk_samples_specimen_type_id_eks')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_samples')),
    sa.UniqueConstraint('code', name=op.f('uq_samples_code')),
    sa.UniqueConstraint('lab_code', name=op.f('uq_samples_lab_code')),
    sa.UniqueConstraint('originating_code', 'originating_institution_id', name=op.f('uq_samples_originating_code_originating_institution_id')),
    sa.UniqueConstraint('sequence_name', name=op.f('uq_samples_sequence_name'))
    )
    op.create_index(op.f('ix_samples_collection_id'), 'samples', ['collection_id'], unique=False)
    op.create_index(op.f('ix_samples_location'), 'samples', ['location'], unique=False)
    op.create_table('sequencingruns',
    sa.Column('code', sa.String(length=16), server_default='', nullable=False),
    sa.Column('serial', sa.String(length=32), server_default='', nullable=False),
    sa.Column('sequencing_provider_id', sa.Integer(), nullable=False),
    sa.Column('sequencing_kit_id', sa.Integer(), nullable=False),
    sa.Column('depthplots', sa.LargeBinary(), server_default='', nullable=False),
    sa.Column('qcreport', sa.LargeBinary(), server_default='', nullable=False),
    sa.Column('remark', sa.Text(), server_default='', nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lastuser_id', sa.Integer(), nullable=True),
    sa.Column('stamp', sa.TIMESTAMP(), nullable=False),
    sa.ForeignKeyConstraint(['lastuser_id'], ['users.id'], name=op.f('fk_sequencingruns_lastuser_id_users')),
    sa.ForeignKeyConstraint(['sequencing_kit_id'], ['eks.id'], name=op.f('fk_sequencingruns_sequencing_kit_id_eks')),
    sa.ForeignKeyConstraint(['sequencing_provider_id'], ['institutions.id'], name=op.f('fk_sequencingruns_sequencing_provider_id_institutions')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_sequencingruns')),
    sa.UniqueConstraint('code', name=op.f('uq_sequencingruns_code')),
    sa.UniqueConstraint('serial', name=op.f('uq_sequencingruns_serial'))
    )
    op.create_table('userdatas',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('key_id', sa.Integer(), nullable=False),
    sa.Column('bindata', sa.LargeBinary(), nullable=False),
    sa.Column('mimetype', sa.String(length=32), nullable=False),
    sa.ForeignKeyConstraint(['key_id'], ['eks.id'], name=op.f('fk_userdatas_key_id_eks')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_userdatas_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_userdatas'))
    )
    op.create_index(op.f('ix_userdatas_key_id'), 'userdatas', ['key_id'], unique=False)
    op.create_index(op.f('ix_userdatas_user_id'), 'userdatas', ['user_id'], unique=False)
    op.create_table('platepositions',
    sa.Column('plate_id', sa.Integer(), nullable=False),
    sa.Column('sample_id', sa.Integer(), nullable=False),
    sa.Column('position', sa.String(length=3), server_default='', nullable=False),
    sa.Column('value', sa.Float(), server_default='-1', nullable=False),
    sa.Column('volume', sa.Float(), server_default='-1', nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lastuser_id', sa.Integer(), nullable=True),
    sa.Column('stamp', sa.TIMESTAMP(), nullable=False),
    sa.ForeignKeyConstraint(['lastuser_id'], ['users.id'], name=op.f('fk_platepositions_lastuser_id_users')),
    sa.ForeignKeyConstraint(['plate_id'], ['plates.id'], name=op.f('fk_platepositions_plate_id_plates')),
    sa.ForeignKeyConstraint(['sample_id'], ['samples.id'], name=op.f('fk_platepositions_sample_id_samples')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_platepositions')),
    sa.UniqueConstraint('plate_id', 'position', name=op.f('uq_platepositions_plate_id_position'))
    )
    op.create_table('sequences',
    sa.Column('sequencingrun_id', sa.Integer(), nullable=False),
    sa.Column('sample_id', sa.Integer(), nullable=False),
    sa.Column('method_id', sa.Integer(), nullable=False),
    sa.Column('accid', sa.String(length=32), nullable=True),
    sa.Column('sequence', sa.Text(), server_default='', nullable=False),
    sa.Column('avg_depth', sa.Integer(), server_default='-1', nullable=False),
    sa.Column('depth_plot', sa.LargeBinary(), server_default='', nullable=False),
    sa.Column('length', sa.Integer(), server_default='-1', nullable=False),
    sa.Column('gaps', sa.Integer(), server_default='-1', nullable=False),
    sa.Column('base_N', sa.Integer(), server_default='-1', nullable=False),
    sa.Column('lineage_1', sa.String(length=16), server_default='', nullable=False),
    sa.Column('prob_1', sa.Float(), server_default='-1', nullable=False),
    sa.Column('lineage_2', sa.String(length=16), server_default='', nullable=False),
    sa.Column('prob_2', sa.Float(), server_default='-1', nullable=False),
    sa.Column('lineage_3', sa.String(length=16), server_default='', nullable=False),
    sa.Column('prob_3', sa.Float(), server_default='-1', nullable=False),
    sa.Column('refid', sa.String(length=32), nullable=True),
    sa.Column('point_mutations', sa.Integer(), server_default='-1', nullable=False),
    sa.Column('aa_mutations', sa.Integer(), server_default='-1', nullable=False),
    sa.Column('inframe_gaps', sa.Integer(), server_default='-1', nullable=False),
    sa.Column('outframe_gaps', sa.Integer(), server_default='-1', nullable=False),
    sa.Column('reads_raw', sa.Integer(), server_default='-1', nullable=False),
    sa.Column('reads_optical_dedup', sa.Integer(), server_default='-1', nullable=False),
    sa.Column('reads_trimmed', sa.Integer(), server_default='-1', nullable=False),
    sa.Column('reads_pp_mapped', sa.Integer(), server_default='-1', nullable=False),
    sa.Column('reads_pcr_dedup', sa.Integer(), server_default='-1', nullable=False),
    sa.Column('reads_consensus_mapped', sa.Integer(), server_default='-1', nullable=False),
    sa.Column('reads_mean_insertsize', sa.Integer(), server_default='-1', nullable=False),
    sa.Column('reads_med_insertsize', sa.Integer(), server_default='-1', nullable=False),
    sa.Column('reads_stddev_insertsize', sa.Integer(), server_default='-1', nullable=False),
    sa.Column('snvs', sa.JSON(), server_default='null', nullable=False),
    sa.Column('aa_change', sa.JSON(), server_default='null', nullable=False),
    sa.Column('remarks', sa.Text(), server_default='', nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lastuser_id', sa.Integer(), nullable=True),
    sa.Column('stamp', sa.TIMESTAMP(), nullable=False),
    sa.ForeignKeyConstraint(['lastuser_id'], ['users.id'], name=op.f('fk_sequences_lastuser_id_users')),
    sa.ForeignKeyConstraint(['method_id'], ['eks.id'], name=op.f('fk_sequences_method_id_eks')),
    sa.ForeignKeyConstraint(['sample_id'], ['samples.id'], name=op.f('fk_sequences_sample_id_samples')),
    sa.ForeignKeyConstraint(['sequencingrun_id'], ['sequencingruns.id'], name=op.f('fk_sequences_sequencingrun_id_sequencingruns')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_sequences')),
    sa.UniqueConstraint('accid', name=op.f('uq_sequences_accid'))
    )
    op.create_table('sequencingruns_plates',
    sa.Column('sequencingrun_id', sa.Integer(), nullable=False),
    sa.Column('plate_id', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lastuser_id', sa.Integer(), nullable=True),
    sa.Column('stamp', sa.TIMESTAMP(), nullable=False),
    sa.ForeignKeyConstraint(['lastuser_id'], ['users.id'], name=op.f('fk_sequencingruns_plates_lastuser_id_users')),
    sa.ForeignKeyConstraint(['plate_id'], ['plates.id'], name=op.f('fk_sequencingruns_plates_plate_id_plates')),
    sa.ForeignKeyConstraint(['sequencingrun_id'], ['sequencingruns.id'], name=op.f('fk_sequencingruns_plates_sequencingrun_id_sequencingruns')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_sequencingruns_plates')),
    sa.UniqueConstraint('sequencingrun_id', 'plate_id', name=op.f('uq_sequencingruns_plates_sequencingrun_id_plate_id'))
    )
    op.create_table('useractionlogs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('actionlog_id', sa.Integer(), nullable=False),
    sa.Column('stamp', sa.TIMESTAMP(), nullable=False),
    sa.ForeignKeyConstraint(['actionlog_id'], ['actionlogs.id'], name=op.f('fk_useractionlogs_actionlog_id_actionlogs')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_useractionlogs_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_useractionlogs')),
    sa.UniqueConstraint('user_id', 'actionlog_id', name=op.f('uq_useractionlogs_user_id_actionlog_id'))
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('useractionlogs')
    op.drop_table('sequencingruns_plates')
    op.drop_table('sequences')
    op.drop_table('platepositions')
    op.drop_index(op.f('ix_userdatas_user_id'), table_name='userdatas')
    op.drop_index(op.f('ix_userdatas_key_id'), table_name='userdatas')
    op.drop_table('userdatas')
    op.drop_table('sequencingruns')
    op.drop_index(op.f('ix_samples_location'), table_name='samples')
    op.drop_index(op.f('ix_samples_collection_id'), table_name='samples')
    op.drop_table('samples')
    op.drop_table('plates')
    op.drop_table('groups_roles')
    op.drop_index(op.f('ix_files_parent_id'), table_name='files')
    op.drop_table('files')
    op.drop_table('collection_institution')
    op.drop_table('actionlogs')
    op.drop_table('users_groups')
    op.drop_table('institutions')
    op.drop_index(op.f('ix_eks_member_of_id'), table_name='eks')
    op.drop_table('eks')
    op.drop_table('datalogs')
    op.drop_table('collections')
    op.drop_index(op.f('ix_users_userclass_id'), table_name='users')
    op.drop_index(op.f('ix_users_primarygroup_id'), table_name='users')
    op.drop_index(op.f('ix_users_lastname'), table_name='users')
    op.drop_index(op.f('ix_users_email2'), table_name='users')
    op.drop_table('users')
    op.drop_table('associated_groups')
    op.drop_table('userclasses')
    op.drop_table('sysregs')
    op.drop_table('syslogs')
    op.drop_table('groups')
    # ### end Alembic commands ###
