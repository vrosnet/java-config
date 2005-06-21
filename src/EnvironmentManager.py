# -*- coding: UTF-8 -*-

# Copyright 2004 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

# Author: Saleem Abdulrasool <compnerd@gentoo.org>
# Maintainer: Gentoo Java Herd <java@gentoo.org>
# Java Subsystem Configuration Utility for Gentoo Linux

# ChangeLog
# Saleem A. <compnerd@gentoo.org>
#     December 30, 2004 - Initial Rewrite
#                       - Based on the collective works of the following:
#                         {karltk,axxo,aether}@gentoo.org

__version__ = '$Revision: 2.0$'[11:-1]

import VM,Package
import os,glob,re

from Errors import *

class EnvironmentManager:
   virtual_machines = {} 
   packages = []
   
   def __init__(self):
      # Get JAVA_HOME
      environ_path = [
                        os.path.join(os.environ.get('HOME'), '.gentoo', 'java'),
                        os.path.join('/', 'etc', 'env.d', '20java')
                     ]

      self.JAVA_HOME = None

      for file in environ_path:
         try:
            stream = open(file, 'r')
         except IOError:
            continue
         
         read = stream.readline()
         while read:
            if read.strip().startswith('JAVA_HOME'):
               stream.close()
               self.JAVA_HOME = read.split('=', 1)[-1].strip()
               break
            else:
               read = stream.readline()
         stream.close()      

      # Collect the Virtual Machines
      # TODO: MAKE THIS MODULAR!
      if os.path.isdir('/etc/env.d/java'):
         try:
            count = 1
            for file in os.listdir('/etc/env.d/java'):
               conf = os.path.join('/etc/env.d/java', file)

               if file.startswith("20"):
                  vm = None

                  try:
                     vm = VM.VM(conf)
                  except InvalidConfigError:
                     pass
                  except PermissionError:
                     pass

                  if vm.query('JAVA_HOME') == self.JAVA_HOME:
                     vm.set_active()

                  self.virtual_machines[count] = vm
                  count += 1
         except OSError:
            pass

      # Collect the packages
      # TODO: MAKE THIS MODULAR!
      packages_path = os.path.join('/', 'usr', 'share', '*', 'package.env')
      for package in iter(glob.glob(packages_path)):
         self.packages.append(Package.Package(package,os.path.basename(os.path.dirname(package))))

   def get_active_vm(self):
      vm_list = self.get_virtual_machines()

      for count in iter(vm_list):
         if vm_list[count].active:
            return vm_list[count]

      raise RuntimeError, "No java vm could be found."

   def get_virtual_machines(self):
      return self.virtual_machines

   def find_vm(self, name):
      found = []
      for id, vm in self.virtual_machines.iteritems():
         if vm.name().startswith(name):
            found.append(vm)
      return found

   def get_packages(self):
      return self.packages

   def query_packages(self, packages, query):
      results = []

      for package in iter(self.get_packages()):
         if package.name in packages:
            value = package.query(query)
            if value:
               results.append(value)
            packages.remove(package.name)

      return results

   def get_vm(self, machine):
      vm_list = self.get_virtual_machines()
      selected = None

      for count in iter(vm_list):
         vm = vm_list[count]

         if str(machine).isdigit():
            if int(machine) is count:
               return vm
         else:
            # Check if the vm is specified via env file
            if machine == vm.filename():
               return vm 

            # Check if the vm is specified by name 
            elif machine == vm.name():
               return vm

            # Check if the vm is specified via JAVA_HOME
            elif machine == vm.query('JAVA_HOME'):
               return vm

            # Check if vm is specified by partial name 
            elif vm.name().startswith(machine):
               selected = vm

      if selected:
         return selected
      else:
         return None

   def create_env_entry(self, vm, stream, render="%s=%s\n"):
      stream.write("# Autogenerated by java-config\n")
      stream.write("# Java Virtual Machine: %s\n\n" % vm.query('VERSION'))

      try:
         ENV_VARS = vm.query('ENV_VARS')
         for (item,value) in vm.get_config().iteritems():
            if item in ENV_VARS:
               stream.write(render % (item,value))
      except IOError:
         raise PermissionError
      except EnvironmentUndefinedError:
         raise EnvironmentUndefinedError

   def set_vm(self, vm, sh_env_file, csh_env_file=None):

      # Create the SH environment file
      if sh_env_file is not None:
         try:
            stream = open(sh_env_file, 'w')
         except IOError:
            raise PermissionError

         try:
            self.create_env_entry(vm, stream, "%s=%s\n")
         except IOError:
            stream.close()
            raise PermissionError
         except EnvironmentUndefinedError:
            stream.close();
            raise EnvironmentUndefinedError

         stream.close()

      # Create the CSH environment file
      if csh_env_file is not None:
         try:
            stream = open(csh_env_file, 'w')
         except IOError:
            raise PermissionError

         try:
            create_env_entry(vm, stream, "setenv %s %s\n")
         except IOError:
            stream.close()
            raise PermissionError

         stream.close()

   def clean_classpath(self, env_file):
      if os.path.isfile(env_file):
         try:
            os.remove(env_file)
         except IOError:
            raise PermissionError

   def set_classpath(self, env_file, pkgs):
      classpath = self.query_packages(pkgs, "CLASSPATH")
      classpath = re.sub(':+', ':', classpath) 
      classpath.strip(':')

      if os.path.isfile(env_file):
         try:
            os.remove(env_file)
         except IOError:
            raise PermissionError

      try:
         stream = open(env_file, 'w')
      except IOError:
         raise PermissionError

      stream.write("CLASSPATH=%s\n" % (classpath))
      stream.close()

   def append_classpath(self, env_file, pkgs):
      classpath = self.query_packages(pkgs, "CLASSPATH")
      classpath = re.sub(':+', ':', classpath) 
      classpath.strip(':')

      oldClasspath = ''
      if os.path.isfile(env_file):
         try:
            stream = open(env_file, 'r')
         except IOError:
            raise PermissionError

         read = stream.readline()
         while read:
            if read.strip().startswith('CLASSPATH'):
               stream.close()
               oldClasspath = read.split('=', 1)[-1].strip()
               break
            else:
               read = stream.readline()
         stream.close()

      classpath = oldClasspath + ':' + classpath

      if os.path.isfile(env_file):
         try:
            os.remove(env_file)
         except IOError:
            raise PermissionError

      try:
         stream = open(env_file, 'w')
      except IOError:
         raise PermissionError

      stream.write("CLASSPATH=%s\n" % (classpath))
      stream.close()
# vim:set expandtab tabstop=3 shiftwidth=3 softtabstop=3:
