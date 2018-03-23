# coding=utf-8
from couchdb.design import ViewDefinition


FIELDS = [
    'tender_id',
    'doc_type',
    'title',
    'status'
]

def add_index_options(doc):
    doc['options'] = {'local_seq': True}


def sync_design(db):
    views = [j for i, j in globals().items() if "_view" in i]
    ViewDefinition.sync_many(db, views, callback=add_index_options)


audits_all_view = ViewDefinition('audits', 'all', '''function(doc) {
    if(doc.doc_type == 'Audit') {
        var fields=%s, data={};
            for (var i in fields) {
                if (doc[fields[i]]) {
                    data[fields[i]] = doc[fields[i]]
                }
            }
        emit(doc.date_modified, data);
    }
}''' % FIELDS)
