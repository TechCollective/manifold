from cement import Handler
from .db_interface import *
from ..models.database.companies import *
import sys

class DBCompaniesHandler(DBInterface, Handler):
    class Meta:
        label = 'db_companies'

    def add(self, company_obj, source):
        company_db = Companies(name=company_obj.name)
        if company_obj.number:
            company_db.number = company_obj.number

        self.app.session.add(company_db)
        self.app.session.commit()
        self.run_hook(company_db, source)
        return company_db

    def delete(self, company_obj):
        pass

    def update(self, company_obj, company_db, source):
        changed = False
        if company_db.name != company_obj.name:
            company_db.name = company_obj.name
            changed = True
        if company_db.number != company_obj.number:
            company_db.number = company_obj.number
            changed = True

        if changed:
            self.app.log.debug("Updating company in DB: [Company: " + company_obj.name + " Source: " + source + "]")
            self.app.session.commit()
            self.run_hook(company_db, source)


    # TODO put this in a hook when the app closes
    #def close_session(self):
    #   self.app.session.close()
    def run_hook(self, obj, source):
        for res in self.app.hook.run('company_update'):
            res(obj, source)