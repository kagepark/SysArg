# Kage Park
# CLI Argument define

import sys
import os
import re
import ast

def IsNone(inp,**opts):
    default=opts.get('default',opts.get('out',True))
    if inp is None: 
       return default
    elif isinstance(inp,(list,tuple,dict,str)):
       if not inp:
           return default
       if opts.get('detail'):
           if isinstance(inp,(list,tuple)) and len(inp) == 1:
               if inp[0] is None:
                   return default
               if isinstance(inp[0],(list,tuple,dict,str)) and not inp[0]:
                   return default
    if isinstance(default,bool):
        return False
    return inp

def space(n=1):
    s=''
    for i in range(0,n):
        s+=' '
    return s

def tap_string(string,fspace=0,nspace=0,new_line='\n',flength=0,nlength=0,ntap=0):
    if isinstance(string,str):
        rc_str=[]
        string_a=string.split(new_line)
        n=space(nspace)
        for ii in range(0,len(string_a)):
            if ii == 0:
                s=space(fspace)
                if flength > 0:
                    for jj in range(0,len(string_a[ii])//flength):
                        rc_str.append(s+string_a[ii][flength*jj:(flength*(jj+1))])
                        if ntap:
                            s=space(nspace)+space(ntap)
                            ntap=0
                    rc_str.append(s+string_a[ii][(flength*(jj+1)):])
                else:
                    rc_str.append(s+string_a[ii])
            else:
                if nlength > 0:
                    for jj in range(0,len(string_a[ii])//nlength):
                        rc_str.append(n+string_a[ii][nlength*jj:(nlength*(jj+1))])
                        if ntap:
                            n=n+space(ntap)
                            ntap=0
                    rc_str.append(n+string_a[ii][(nlength*(jj+1)):])
                else:
                    rc_str.append(n+string_a[ii])
        return new_line.join(rc_str)
    return space(fspace)+'{}'.format(string)

def TypeData(_type,data,spliter=None):
    if _type is str:
        return '{}'.format(data)
    elif _type is int:
        try:
            return int(data)
        except:
            return False
    elif _type in [list,dict,tuple]:
        if isinstance(data,str):
            try:
                data=ast.literal_eval(data)
            except:
                if spliter:
                    if _type is list : return data.split(spliter)
                    if _type is tuple : return tuple(data.split(spliter))
                return False
    if isinstance(data,_type):
        return data
    return False


class SysArg:
    '''
SysArg()
  program: Program name
  desc: Program Description
  epilog: Program Epilog (tail string of the help)
  help_desc: special Help description
defind()
  name: (required) parameter name
  short: short parameter(-XX)
  long: long parameter(--XX)
  params: 
     default:0(found parameter then True), 
     0<n: how many required parameter input data(number)
     - : until next parameter or until finished inputs
  params_name: --abc=<PARAMS_NAME(Explain String)> (this format)
  required: required parameter (default False, need then True)
  default: default value when no input
  type: default str, if you want int value then change to int, wrong type then not taken
  group: make a special group's prameters
  group_desc: group desciption
    '''
    def __init__(self,*args,**opts):
        if not args:
            self.argv=tuple(sys.argv[:])
            self.args=sys.argv
        else:
            self.argv=tuple(args[:])
            self.args=args
        self.program=opts.get('program') 
        self.cmd_id=opts.get('cmd_id',0) 
        self.desc=opts.get('desc') 
        self.epilog=opts.get('epilog') 
        self.option={}
        self.group={}
        self.commands=[]
        self.version=opts.get('version')
        self.help_desc=opts.get('help_desc','Help') 

    def error_exit(self,msg):
        print(msg)
        os._exit(1)

    def define(self,name=None,**opts):
        if name in self.option:
            self.error_exit('Already defined "{}" parameter name'.format(name))
        _short=opts.get('short')
        _long=opts.get('long')
        _params_name=opts.get('params_name') # something : --time=SOMETHING, None: --time WORD
        if _params_name:
            _params=1
        else:
            _params=opts.get('params',0) #how many parameters
        _type=opts.get('type',str) #Data type
        _desc=opts.get('desc')
        _default=opts.get('default')
        _group=opts.get('group')
        _group_desc=opts.get('group_desc')
        _required=opts.get('required',False)
        _command=opts.get('command',False)
        _select=opts.get('select',[])
        _spliter=opts.get('spliter',None) #list or tuple case but input is string
        _arg=opts.get('arg',False)
        if IsNone(name) and  not _command and not _arg:
            if _short:
                self.error_exit('Required parameter name for option at {}'.format(_short))
            else:
                self.error_exit('Required parameter name for option at {}'.format(_long))

        _value=[]
        # location parameter(value)
        if not _short and not _long and len(self.argv) > _params:
            _value=self.argv[_params]
            if _value in self.args: self.args.remove(_value)
        else:
            # Check same option
            for cc in self.option:
                if _short and self.option[cc].get('short') == _short:
                    self.error_exit('ERROR: Already "{} of {}" defined at {}'.format(_short,name,cc))
                if _long and self.option[cc].get('long') == _long:
                    self.error_exit('ERROR: Already "{} of {}" defined at {}'.format(_long,name,cc))
            # Check same option in each group
            if _group in self.group: 
                for cc in self.group[_group]:
                    if not isinstance(self.group[_group][cc],dict): continue
                    if _short and self.group[_group][cc].get('short') == _short:
                        self.error_exit('ERROR: Already "{} of {}" defined at {} in {}'.format(_short,name,cc,_group))
                    if _long and self.group[_group][cc].get('long') == _long:
                        self.error_exit('ERROR: Already "{} of {}" defined at {} in {}'.format(_long,name,cc,_group))

            # Check parameter
            if _params == 0:
                if _long in self.args:
                    _value=True
                    self.args.remove(_long)
                elif _short:
                    if _short in self.args:
                        _value=True
                        self.args.remove(_short)
                    else:
                        for ii in range(0,len(self.args)):
                            if re.match(r'-[a-zA-Z0-9]',self.args[ii]):
                                if _short[1:] in self.args[ii]:
                                    _value=True
                                    i=self.args[ii].index(_short[1:])
                                    self.args[ii]=self.args[ii][:i]+self.args[ii][i+len(_short[1:]):]                
            # Input parameter
            else:
                if _long and _params_name:
                    _params=1
                    tt=[]
                    for ii in self.args:
                        if ii.startswith('{}='.format(_long)):
                            __v__=TypeData(_type,ii.split('=')[1],_spliter)
                            if __v__ is False:
                                self.error_exit('ERROR: Wrong input type format at {}, it required {}'.format(_long,_type.__name___)) 
                            _value.append(__v__)
                        else:
                            tt.append(ii)
                    self.args=tt
                if not _value:
                    tt=[]
                    for ii in range(0,len(self.args)):
                        if _short == self.args[ii] or (_long == self.args[ii] and not _params_name):
                            if _params == '-':
                                for jj in range(ii+1,len(self.args)):
                                    if self.args[jj][0] == '-':
                                        break
                                    __v__=TypeData(_type,self.args[jj],_spliter)
                                    if __v__ is False:
                                        self.error_exit('ERROR: Wrong input type format at {}, it required {}'.format(_short if _short else _long,_type.__name__)) 
                                    _value.append(__v__)
                                break
                                tt=tt+self.args[jj+1:]
                            elif isinstance(_params,int) and len(self.args) >= ii+1+_params:
                                for jj in range(0,_params):
                                    if self.args[ii+1+jj][0] == '-':
                                        break
                                    __v__=TypeData(_type,self.args[ii+1+jj],_spliter)
                                    if __v__ is False:
                                        self.error_exit('ERROR: Wrong input type format at {}, it required {}'.format(_short if _short else _long,_type.__name__)) 
                                    _value.append(__v__)
                                if len(_value) == _params:
                                    tt=tt+self.args[ii+jj+2:]
                                    break
                                else:
                                    _value=[]
                                    tt=tt+self.args[ii:]
                        else:
                            tt.append(self.args[ii])
                    self.args=tt
            
        if _group:
            if _command:
                if _group not in self.commands: self.commands.append(_group)
            if _group not in self.group: self.group[_group]={}
            if _command:
                self.group[_group]['command']=_command
                #If command has _select and arg then this command should be need input arg value in selection
                if _arg:
                    self.group[_group]['arg']=True
                    if _select:
                        self.group[_group]['select']=_select
                        if not self.__dict__.get('args'):
                            if _default: self.group[_group]['value']=_default
                        #elif self.__dict__.get('args')[0] in _select:
                        else: #put any data (even if wrong data)
                            self.group[_group]['value']=self.__dict__.get('args')[0]
                            del self.__dict__['args'][0]
                    else:
                        if int(self.__dict__.get('args')) > 0:
                            self.group[_group]['value']=self.__dict__.get('args')[0]
                            del self.__dict__['args'][0]
            else:
                self.group[_group][name]={
                    'short':_short,
                    'long':_long,
                    'params':_params,
                    'params_name':_params_name,
                    'type':_type,
                    'desc':_desc,
                    'value':_value,
                    'default':_default,
                    'required':_required,
                    'spliter':_spliter,
                    'select':_select,
                }
            if _group_desc: self.group[_group]['desc']=_group_desc
        else:
            self.option[name]={
                'short':_short,
                'long':_long,
                'params':_params,
                'params_name':_params_name,
                'type':_type,
                'desc':_desc,
                'value':_value,
                'default':_default,
                'required':_required,
                'spliter':_spliter,
                'select':_select,
            }

    def Cmd(self,name=None):
        if self.cmd_id == 0 : return self.argv[0]
        if len(self.argv) > self.cmd_id:
            if self.argv[self.cmd_id] in self.commands:
                if name:
                    if self.argv[self.cmd_id] == name:
                        self.Check(group=name)
                        return True
                    return False
                self.Check(group=self.argv[self.cmd_id])
                return self.argv[self.cmd_id]
            if self.argv[self.cmd_id] not in ['--version','--help']:
                print(':: Wrong command "{}"\n'.format(self.argv[self.cmd_id]))
        else:
            print(':: Require some command\n')
        self.Help(call=True)

    def Get(self,name=None,group=None,mode='auto'):
        def Val(data,mode='auto'):
            if isinstance(data,dict):
                vv=data.get('value')
                if IsNone(vv):
                    vv=data.get('default')
                if data.get('select'):
                    if vv in data.get('select'):
                        return vv
                    else:
                        self.error_exit('ERROR: Wrong input({}). it should be one of {}'.format(vv,data['select']))
                if mode == 'auto':
                    if isinstance(vv,list) and len(vv) == 1:
                        return vv[0]
                return vv

        if group and group in self.group:
            if name:
                return IsNone(Val(self.group[group][name]),out=None)
            return IsNone(Val(self.group[group]),out=None)
        elif name in self.option:
            return IsNone(Val(self.option[name]),out=None)
        else:
            rt={}
            if not name and not group:
                for o in self.option:
                    rt[o]=IsNone(Val(self.option[o]),out=None)
                for g in self.group:
                    if g not in rt: rt[g]={}
                    for o in self.group[g]:
                        if isinstance(self.group[g][o],dict):
                            rt[g][o]=IsNone(Val(self.group[g][o]),out=None)
            elif not name and group and group in self.group:
                rt[group]={}
                for o in self.group[group]:
                    if isinstance(self.group[group][o],dict):
                        rt[group][o]=IsNone(Val(self.group[group][o]),out=None)
            return IsNone(rt,out=None)


    def Check(self,group=None):
        if group and group in self.group:
            for name in self.group[group]:
                if isinstance(self.group[group][name],dict) and self.group[group][name].get('required'):
                    if IsNone(self.group[group][name].get('value')):
                        if IsNone(self.group[group][name].get('default')):
                            print(':: Missing required option "{}" of {}\n'.format(name,group))
                            self.Help(call=True)
        for name in self.option:
            if self.option[name].get('required'):
                if IsNone(self.option[name].get('value')):
                    if IsNone(self.option[name].get('default')):
                        print(':: Missing required option "{}"\n'.format(name))
                        self.Help(call=True)
        
    def Version(self,version=None,call=False,new_line='\n'):
        if (version or self.version) and '--version' in sys.argv:
            if version:
                sys.stdout.write(version)
            else:
                sys.stdout.write(self.version)
            if new_line: sys.stdout.write(new_line)
            sys.stdout.flush()
            os._exit(0)

    def Help(self,Short='-h',Long='--help',call=False,short_len=5,long_len=30,desc_space=2):
       #######################
       #Description Design
       #######################
       def mk_desc(_desc,default=None,required=False,nspace=short_len+long_len+desc_space,_type=None,_params=None,_params_name=None,_spliter=None,_select=None):
           if _desc:
               if default:
                   _desc=_desc+'(default:{})'.format(default)
               if required:
                   _desc=_desc+'(required)'
           else:
               if default:
                   _desc='default:{}'.format(default)
               if required:
                   if _desc:
                       _desc=_desc+',required'
                   else:
                       _desc='required'
           if _select:
               _desc=_desc+'(choose:{})'.format(_select)
           elif _type and _params_name is None:
               s = 'N' if _type is int \
                   else 'V{0}V{0}..'.format(_spliter) if _type is list and _spliter \
                   else 'V V ..' if _type is list and ((isinstance(_params,int) and _params > 1) or _params == '-') \
                   else '[V,V,..]' if _type is list \
                   else 'V{0}V{0}..' if _type is tuple and _spliter \
                   else 'V V ..' if _type is tuple and ((isinstance(_params,int) and _params > 1) or _params =='-')\
                   else '(V,V,..)' if _type is tuple \
                   else "{'S':'V',..}" if _type is dict \
                   else 'S'
                       
               if isinstance(_params,int) and _params:
                   if _params==1:
                       _desc=_desc+'(input({}):{})'.format(_params,s)
                   else:
                       if _spliter:
                           _desc=_desc+'(input({0}):{1})'.format(_params,s)
                       else:
                           if ' ' in s:
                               _desc=_desc+'(input({0}):{1})'.format(_params,s)
                           else:
                               _desc=_desc+'(input({0}):{1}1 {1}2 ...)'.format(_params,s)
               elif _params == '-':
                   if _spliter:
                       _desc=_desc+'(input:{0})'.format(s)
                   else:
                       if ' ' in s:
                           _desc=_desc+'(input:{0})'.format(s)
                       else:
                           _desc=_desc+'(input:{0}1 {0}2 ...)'.format(s)
           if _desc: 
               return tap_string(_desc,nspace=nspace)
           return ''

       #######################
       #Option Design
       #######################
       def print_option(data):
           if isinstance(data,dict):
               _desc=mk_desc(data.get('desc'),default=data.get('default'),required=data.get('required'),nspace=short_len+long_len+desc_space,_type=data.get('type'),_params=data.get('params'),_params_name=data.get('params_name'),_spliter=data.get('spliter'),_select=data.get('select'))
               if data.get('short') and data.get('long'):
                   if len(data.get('short')) > short_len:
                       sss=long_len-(len(data.get('short'))-short_len)
                   else:
                       sss=long_len
                   if data.get('params_name'):
                       print('%{}s, %-{}s%s'.format(short_len,sss)%(data.get('short'),'{}={}'.format(data.get('long'),data.get('params_name')),_desc))
                   else:
                       print('%{}s, %-{}s%s'.format(short_len,sss)%(data.get('short'),data.get('long'),_desc))
               elif data.get('short'):
                   if len(data.get('short')) > short_len:
                       sss=long_len-(len(data.get('short'))-short_len)
                   else:
                       sss=long_len
                   print('%{}s  %s%s'.format(short_len)%(data.get('short'),space(sss),_desc))
               elif data.get('long'):
                   if data.get('params_name'):
                       print('%s  %-{}s%s'.format(long_len)%(space(short_len),'{}={}'.format(data.get('long'),data.get('params_name')),_desc))
                   else:
                       print('%s  %-{}s%s'.format(long_len)%(space(short_len),data.get('long'),_desc))


       #######################
       #Print Help(Main Design)
       #######################
       if call or (Short and Short in self.args) or (Long and Long in self.args):
           if self.cmd_id > 0 and not self.commands:
                print("ERROR: defined extra command at SysArg(..,cmd_id=N).\nIt required defineing command with SysArg.define(...,group=<cmd name>,command=True)")
                os._exit(1) 

           #Print Program
           if self.program:
               if self.option:
                   if self.commands:
                       print('Usage: {} <command> [OPTION] [<args>]'.format(self.program))
                   else:
                       print('Usage: {} [OPTION] [<args>]'.format(self.program))
               else:
                   if self.commands:
                       print('Usage: {} <command> [<args>]'.format(self.program))
                   else:
                       print('Usage: {} [<args>]'.format(self.program))
               if self.version:
                   print('Version: {}'.format(self.version))

           #Print Special Group Option
           if self.commands and self.cmd_id > 0 and len(self.argv) > self.cmd_id and self.argv[self.cmd_id] in self.commands:
               if self.group[self.argv[self.cmd_id]].get('command'):
                   if self.group[self.argv[self.cmd_id]].get('desc'):
                       _group_desc=tap_string(self.group[self.argv[self.cmd_id]]['desc'],nspace=short_len+long_len+desc_space)
                       print('* %-{}s  %s'.format(short_len+long_len-2)%(self.argv[self.cmd_id],_group_desc))
                   else:
                       print('* %-{}s'.format(short_len+long_len-2)%(self.argv[self.cmd_id]))
               for oo in self.group[self.argv[self.cmd_id]]:
                   print_option(self.group[self.argv[self.cmd_id]][oo])
               os._exit(0)

           #Print Desc
           if self.desc:
               print(self.desc)

           #Commands Help
           if self.commands:
               print('\nSupported <command>s are:')
               for cc in self.commands:
                   if self.group.get(cc,{}).get('desc'):
                       _group_desc=tap_string(self.group[cc]['desc'],nspace=short_len+long_len+desc_space)
                       if self.group.get(cc,{}).get('arg'): # required argument
                           print('  %-{}s%s'.format(short_len+long_len)%('{} [OPT] <arg>'.format(cc),_group_desc))
                       else:
                           print('  %-{}s%s'.format(short_len+long_len)%(cc,_group_desc))
                   else:
                       print('  %-{}s'.format(short_len+long_len)%(cc))

           #Print Help
           print('\n[OPTION]')
           _help_desc=tap_string(self.help_desc,nspace=short_len+long_len+desc_space)
           if Short and Long:
               print('%{}s, %-{}s%s'.format(short_len,long_len)%(Short,Long,_help_desc))
           elif Long:
               print('%s  %-{}s%s'.format(long_len)%(space(short_len),Long,_help_desc))
           elif Short and Long:
               print('%{}s  %s'.format(short_len)%(Short,space(long_len),_help_desc))
            
           #Print Option
           for oo in self.option:
               print_option(self.option[oo])

           #Print Group Option
           for gg in self.group:
               if self.group[gg].get('command'):
                   #if command but no option then ignore
                   if len(self.group[gg]) < 6: continue
              #Make a same condition as normal group to command group
              #     print()
              #     if self.group[gg].get('desc'):
              #         _group_desc=tap_string(self.group[gg]['desc'],nspace=short_len+long_len+desc_space)
              #         print('* %-{}s  %s'.format(short_len+long_len-2)%(gg,_group_desc))
              #     else:
              #         print('* %-{}s'.format(short_len+long_len-2)%(gg))
              # else:
              #     print()
              #     if self.group[gg].get('desc'):
              #         _group_desc=tap_string(self.group[gg]['desc'],nspace=short_len+long_len+desc_space)
              #         print('%-{}s%s'.format(short_len+long_len)%('[ {} ]'.format(gg),_group_desc))
              #     else:
              #         print('%-{}s'.format(short_len+long_len)%('[ {} ]'.format(gg)))
               print()
               if self.group[gg].get('desc'):
                   _group_desc=tap_string(self.group[gg]['desc'],nspace=short_len+long_len+desc_space)
                   print('%-{}s%s'.format(short_len+long_len)%(' * {}'.format(gg),_group_desc))
               else:
                   print('%-{}s'.format(short_len+long_len)%(' * {}'.format(gg)))
               for oo in self.group[gg]:
                   print_option(self.group[gg][oo])

           #Print Epilog
           if self.epilog:
               print(self.epilog)
           os._exit(0)
            
    def Args(self):
        return self.__dict__.get('args')
