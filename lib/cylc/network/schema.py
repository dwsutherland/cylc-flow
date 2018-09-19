#!/usr/bin/env python2

# THIS FILE IS PART OF THE CYLC SUITE ENGINE.
# Copyright (C) 2008-2018 NIWA & British Crown (Met Office) & Contributors.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""GraphQL API schema via Graphene implementation."""


import graphene

class API(graphene.ObjectType):
    version = graphene.Int()
    greeting = graphene.String()

class Query(graphene.ObjectType):
    hello = graphene.String(name=graphene.String(default_value="stranger"))
    api = graphene.Field(API)

    def resolve_hello(self, info, name):
        print("HELLLLOOOO")
        return 'Hello ' + name

    def resolve_api(self, info):
        schd_func = info.context.get('schd_obj').about_api()
        API.version = schd_func['version']
        return API 


schema = graphene.Schema(query=Query)

