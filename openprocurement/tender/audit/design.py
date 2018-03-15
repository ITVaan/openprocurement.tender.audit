# coding=utf-8
from couchdb.design import ViewDefinition


def add_index_options(doc):
    doc['options'] = {'local_seq': True}


def sync_design(db):
    views = [j for i, j in globals().items() if "_view" in i]
    ViewDefinition.sync_many(db, views, callback=add_index_options)


audits_all_view = ViewDefinition('audits', 'all', '''function(doc) {
    if(doc.doc_type == 'Audit') {
        emit(doc.auditID, null);
    }
}''')
