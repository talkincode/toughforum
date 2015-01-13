#!/usr/bin/env python3

from tornweb.webutils import route,authenticated,auth_admin
from tornweb.utils import md5hash,get_uuid,get_currtime
from .base import BasicHandler
from tornweb.base import ApiMessage
from tornweb.btform import webform,rules
from tornweb.btform.rules import input_style,button_style
from tornado import gen
from db_models import CoeOption


def option_update_form(coe_options):
    _inputs = []
    for opt in coe_options:
        _inputs.append(webform.Textbox(
            opt.option_name, 
            rules.len_of(0, 255), 
            description=opt.option_desc, 
            size=255,
            value=opt.option_value, 
            required="required",**input_style) )
    _inputs.append(webform.Button("submit", type="submit", html=u"<b>更新</b>", **button_style))
    return webform.Form(*_inputs,title=u"系统参数更新",action="/manage/options")()

@route('/manage/options')
class OptionsHandler(BasicHandler):

    @auth_admin
    def get(self, template_variables={}):
        opts = self.db.query(CoeOption).all()
        form = option_update_form(opts)
        self.render("manage/base_form.html",form=form)

    @auth_admin
    def post(self, *args, **kwargs):
        opts = self.db.query(CoeOption).all()
        form = option_update_form(opts)
        if not form.validates(source=self.get_params()):
            return self.render("manage/base_form.html", form=form)
        
        for opt in opts:
            self.db.execute(
                "update coe_option set option_value = :val where option_name = :name",
                {'name':opt.option_name,'val':form.d[opt.option_name]})

        self.db.commit()
        self.redirect('/manage/options', permanent=False)        
