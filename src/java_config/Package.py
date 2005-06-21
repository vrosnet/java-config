# -*- coding: UTF-8 -*-

# Copyright 2004-2005 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

import EnvFileParser

class Package:
   def __init__(self,file, name):
      self.file = file
      self.name = name
      self.config = EnvFileParser.EnvFileParser(file).get_config()

   def name(self):
      return self.name

   def file(self):
      return self.file

   def description(self):
      if self.config.has_key("DESCRIPTION"):
         return self.config["DESCRIPTION"]
      else:
         return "No Description"

   def classpath(self):
      if self.config.has_key("CLASSPATH"):
         return self.config["CLASSPATH"]
      else:
         return None

   def query(self, var):
      if self.config.has_key(var):
         return self.config[var]
      else:
         return None

# vim:set expandtab tabstop=3 shiftwidth=3 softtabstop=3: