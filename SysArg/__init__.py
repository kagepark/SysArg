import os
import re
import ast
import sys
import getpass
from kmport import *

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
            self.args=sys.argv[:]
        else:
            self.argv=tuple(args[:])
            self.args=list(args[:])
        self.argo=[]
        self.program=opts.get('program')
        self.cmd_id=opts.get('cmd_id',0)
        if len(self.args) > self.cmd_id:
            del self.args[self.cmd_id]
        self.desc=opts.get('desc')
        self.epilog=opts.get('epilog')
        self.option={}
        self.group={}
        self.commands={}
        self.version=opts.get('version')
        self.help_desc=opts.get('help_desc','Help')
        self.ask=opts.get('ask',False)
        self.SysArg_hidden_show=opts.get('SysArg_hidden_show','SysArg_hidden_show')
        self.gtmp={}
    def error_exit(self,msg):
        sys.stderr.write('{}\n'.format(msg))
        sys.stderr.flush()
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
        _cmd_id=opts.get('cmd_id',1)
        _combin=opts.get('combin',False)
        _hidden=opts.get('hidden',False)
        if IsNone(name) and  not _command and not _arg:
            if _short:
                self.error_exit('Required parameter name for option at {}'.format(_short))
            else:
                self.error_exit('Required parameter name for option at {}'.format(_long))
        # Filter wrong ordering
        if _command and _group in self.group:
            self.error_exit('ERROR: Please define command group first\n  0. arg=SysArg.SysArg()\n  1. Define command group\n  2. Global options\n  3. Group Options')

        # location parameter(value)
        _value=[]
        if not _short and not _long and len(self.argv) > _params:
            _value=self.argv[_params]
            if not _command and _value in self.args:
                if _value not in self.argo: self.argo.append(_value)
                self.args.remove(_value)
        else:
            # Filter for any option in global option
            for cc in self.option:
                if _short and self.option[cc].get('short') == _short:
                    self.error_exit('ERROR: Already "{} of {}" defined at global option {}'.format(_short,name,cc))
                if _long and self.option[cc].get('long') == _long:
                    self.error_exit('ERROR: Already "{} of {}" defined at global option {}'.format(_long,name,cc))
            # Filter for global option in group option
            # or
            # Filter for not command group option in other command group option
            if not _group or (not _command and _group and _group not in self.commands):
                mm='global' if not _group else '''group {}'s'''.format(_group)
                for gg in self.group:
                    for cc in self.group[gg]:
                        if not isinstance(self.group[gg][cc],dict): continue
                        if _short and self.group[gg][cc].get('short') == _short:
                            self.error_exit('''ERROR: Already {} "{} of {}" defined at {} in group {}'''.format(mm,_short,name,cc,gg))
                        if _long and self.group[gg][cc].get('long') == _long:
                            self.error_exit('''ERROR: Already {} "{} of {}" defined at {} in group {}'''.format(mm,_long,name,cc,gg))
            # Filter for group option in same group option
            if _group in self.group:
                for cc in self.group[_group]:
                    if not isinstance(self.group[_group][cc],dict): continue
                    if _short and self.group[_group][cc].get('short') == _short:
                        self.error_exit('ERROR: Already "{} of {}" defined at {} in same group {}'.format(_short,name,cc,_group))
                    if _long and self.group[_group][cc].get('long') == _long:
                        self.error_exit('ERROR: Already "{} of {}" defined at {} in same group {}'.format(_long,name,cc,_group))

            # Check parameter
            if _params == 0:
                if _long in self.args:
                    _value=True
                    if _long not in self.argo: self.argo.append(_long)
                    self.args.remove(_long)
                elif _short:
                    if _short in self.args:
                        _value=True
                        if _short not in self.argo: self.argo.append(_short)
                        self.args.remove(_short)
                    elif _combin: # check combin data in short
                        for ii in range(0,len(self.args)):
                            if re.match(r'-[a-zA-Z0-9]',self.args[ii]):
                                if _short[1:] in self.args[ii]:
                                    #Global's combin short option(not _group) or command's short option of combin(_group == self.argv[_cmd_id])
                                    if not _group or _group == self.argv[_cmd_id]:
                                        _value=True
                                        i=self.args[ii].index(_short[1:])
                                        self.args[ii]=self.args[ii][:i]+self.args[ii][i+len(_short[1:]):]
                                        if _short not in self.argo: self.argo.append(_short)
            # Input parameter
            else:
                if _long and _params_name:
                    _params=1
                    tt=[]
                    for ii in self.args:
                        if ii.startswith('{}='.format(_long)):
                            __v__=TypeData(ii.split('=')[1],want_type=_type,spliter=_spliter)
                            if __v__ is False:
                                if self.ask:
                                    iii=cli_input('Wrong input type format at {}, it required {}! Please type it:'.format(_short if _short else _long,_type.__name__))
                                    if not IsNone(iii):
                                        __v__=TypeData(iii,want_type=_type,spliter=_spliter)
                                        if __v__ is False:
                                            self.error_exit('ERROR: Wrong input type format at {}, it required {}'.format(_short if _short else _long,_type.__name__))
                                        _value.append(__v__)
                                else:
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
                                    __v__=TypeData(self.args[jj],want_type=_type,spliter=_spliter)
                                    if __v__ is False:
                                        if self.ask:
                                            iii=cli_input('Wrong input type format at {}, it required {}! Please type it:'.format(_short if _short else _long,_type.__name__))
                                            if not IsNone(iii):
                                                __v__=TypeData(iii,want_type=_type,spliter=_spliter)
                                                if __v__ is False:
                                                    self.error_exit('ERROR: Wrong input type format at {}, it required {}'.format(_short if _short else _long,_type.__name__))
                                                _value.append(__v__)
                                        else:
                                            self.error_exit('ERROR: Wrong input type format at {}, it required {}'.format(_short if _short else _long,_type.__name__))
                                    _value.append(__v__)
                                break
                                tt=tt+self.args[jj+1:]
                            elif isinstance(_params,int) and len(self.args) >= ii+1+_params:
                                for jj in range(0,_params):
                                    if self.args[ii+1+jj][0] == '-':
                                        break
                                    __v__=TypeData(self.args[ii+1+jj],want_type=_type,spliter=_spliter)
                                    if __v__ is False:
                                        if self.ask:
                                            iii=cli_input('Wrong input type format at {}, it required {}! Please type it:'.format(_short if _short else _long,_type.__name__))
                                            if not IsNone(iii):
                                                __v__=TypeData(iii,want_type=_type,spliter=_spliter)
                                                if __v__ is False:
                                                    self.error_exit('ERROR: Wrong input type format at {}, it required {}'.format(_short if _short else _long,_type.__name__))
                                                _value.append(__v__)
                                        else:
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
                if _group not in self.commands:self.commands[_group]=_cmd_id
            if _group not in self.group: self.group[_group]={}
            if _command:
                self.group[_group]['command']=_command
                if _hidden: self.group[_group]['hidden']=_hidden
                #If command has _select and arg then this command should be need input arg value in selection
                if _arg:
                    self.group[_group]['arg']=True
                    if _select:
                        self.group[_group]['select']=_select
                        if not self.__dict__.get('args'):
                            if _default: self.group[_group]['value']=_default
                        else: #put any data (even if wrong data)
                            self.group[_group]['value']=self.__dict__.get('args')[0]
                            del self.__dict__['args'][0]
                    else:
                        if int(self.__dict__.get('args')) > 0:
                            self.group[_group]['value']=self.__dict__.get('args')[0]
                            del self.__dict__['args'][0]
            else:
                #Temporary save value at global for command group data
                if self.argv[0] != self.Cmd() and _group in self.commands:
                    if _value:
                        self.gtmp[_group]={'short':_short,'long':_long,'value':_value}
                        _value=[]
                    #If same command and group then put the data to my group
                    if _group == self.Cmd():
                        __value=[]
                        for gg in self.gtmp:
                            if _short == self.gtmp[gg]['short'] or _long == self.gtmp[gg]['long']:
                                __value=self.gtmp[gg]['value']
                                break
                        if __value:
                            self.gtmp.pop(gg)
                            _value=__value
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
                    'combin':_combin,
                    'hidden':_hidden,
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
                'combin':_combin,
                'hidden':_hidden,
            }
    def Cmd(self,name=None,cmd_group=False):
        sys_argvn=len(sys.argv)
        # name is current right command?
        if name:
            if name in self.commands:
                if sys_argvn > self.commands[name] and sys.argv[self.commands[name]] == name:
                    self.Check(group=name)
                    if len(self.args) > self.commands[name] and self.args[self.commands[name]-1] == name:
                        del self.args[self.commands[name]-1]
                    return True
            else:
                if sys_argvn > self.cmd_id and sys.argv[self.cmd_id] == name:
                    del self.args[self.cmd_id]
                    return True
            return False
        # What is currently my command?
        for i in self.commands:
            if sys_argvn > self.commands[i] and sys.argv[self.commands[i]] == i:
                if len(self.args) > self.commands[i] and self.args[self.commands[i]-1] == i:
                    del self.args[self.commands[i]-1]
                self.Check(group=i)
                return i
        if cmd_group:
            print('! Can not find right command!\n')
        else:
            if self.cmd_id < sys_argvn:
                self.Check(group=self.argv[self.cmd_id])
                if len(self.args) > self.cmd_id and self.args[self.cmd_id] == self.argv[self.cmd_id]:
                    del self.args[self.cmd_id]
                return self.argv[self.cmd_id]
            else:
                print(':: Require some command, check cmd_id=N in SysArg()\n')
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
                return Val(self.group[group][name])
            return Val(self.group[group])
        elif name in self.option:
            return Val(self.option[name])
        else:
            rt={}
            if not name and not group:
                for o in self.option:
                    rt[o]=Val(self.option[o])
                for g in self.group:
                    if g not in rt: rt[g]={}
                    for o in self.group[g]:
                        if isinstance(self.group[g][o],dict):
                            rt[g][o]=Val(self.group[g][o])
            elif not name and group and group in self.group:
                rt[group]={}
                for o in self.group[group]:
                    if isinstance(self.group[group][o],dict):
                        rt[group][o]=IsNone(Val(self.group[group][o]),out=None)
            return rt
    def Check(self,group=None):
        if group and group in self.group:
            for name in self.group[group]:
                if isinstance(self.group[group][name],dict) and self.group[group][name].get('required'):
                    if IsNone(self.group[group][name].get('value')):
                        if IsNone(self.group[group][name].get('default')):
                            aa=self.group[group][name].get('long') if self.group[group][name].get('long') else self.group[group][name].get('short')
                            if self.ask:
                                iii=cli_input('Missing "{}({})" parameter! Please type it:'.format(aa,name))
                                if not IsNone(iii):
                                    self.group[group][name]['value']=iii
                            else:
                                sys.stdout.write('\n!! Missing required option "{}({})" of {} !!\n\n'.format(aa,name,group))
                                sys.stdout.flush()
                                self.Help(call=True,command=group)
        for name in self.option:
            if self.option[name].get('required'):
                if IsNone(self.option[name].get('value')):
                    if IsNone(self.option[name].get('default')):
                        aa=self.option[name].get('long') if self.option[name].get('long') else self.option[name].get('short')
                        if self.ask:
                            iii=cli_input('Missing "{}({})" parameter! Please type it:'.format(aa,name))
                            if not IsNone(iii):
                                self.option[name]['value']=iii
                        else:
                            sys.stdout.write('\n!! Missing required option "{}({})" !!\n\n'.format(name,aa))
                            sys.stdout.flush()
                            self.Help(call=True)
    def Version(self,version=None,call=False,new_line='\n'):
        if (version or self.version) and '--version' in sys.argv:
            if version:
                sys.stdout.write('{}'.format(version))
            elif self.version:
                sys.stdout.write('{}'.format(self.version))
            else:
                sys.stdout.write('No version information')
            if new_line: sys.stdout.write(new_line)
            sys.stdout.flush()
            os._exit(0)
    def Help(self,Short='-h',Long='--help',call=False,short_len=5,long_len=30,desc_space=2,command=None,ignore_unknown_command=False):
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
               return WrapString(_desc,nspace=nspace)
           return ''
       #######################
       #Option Design
       #######################
       def print_option(data):
           force=Variable(self.SysArg_hidden_show,default=False,mode='all')
           if isinstance(data,dict):
               if not force and data.get('hidden'): return
               _desc=mk_desc(data.get('desc'),default=data.get('default'),required=data.get('required'),nspace=short_len+long_len+desc_space,_type=data.get('type'),_params=data.get('params'),_params_name=data.get('params_name'),_spliter=data.get('spliter'),_select=data.get('select'))
               if data.get('short') and data.get('long'):
                   if len(data.get('short')) > short_len:
                       sss=long_len-(len(data.get('short'))-short_len)
                   else:
                       sss=long_len
                   if data.get('params_name'):
                       sys.stdout.write('%{}s, %-{}s%s\n'.format(short_len,sss)%(data.get('short'),'{}={}'.format(data.get('long'),data.get('params_name')),_desc))
                   else:
                       sys.stdout.write('%{}s, %-{}s%s\n'.format(short_len,sss)%(data.get('short'),data.get('long'),_desc))
                   sys.stdout.flush()
               elif data.get('short'):
                   if len(data.get('short')) > short_len:
                       sss=long_len-(len(data.get('short'))-short_len)
                   else:
                       sss=long_len
                   sys.stdout.write('%{}s  %s%s\n'.format(short_len)%(data.get('short'),Space(sss),_desc))
                   sys.stdout.flush()
               elif data.get('long'):
                   if data.get('params_name'):
                       sys.stdout.write('%s  %-{}s%s\n'.format(long_len)%(Space(short_len),'{}={}'.format(data.get('long'),data.get('params_name')),_desc))
                   else:
                       sys.stdout.write('%s  %-{}s%s\n'.format(long_len)%(Space(short_len),data.get('long'),_desc))
                   sys.stdout.flush()
       # If exist command then print help for the command only (show all)
       if Short in self.argv:
           ii=self.argv.index(Short)
           if ii > 0:
               command=self.argv[ii-1]
       if Long in self.argv:
           ii=self.argv.index(Long)
           if ii> 0:
               command=self.argv[ii-1]
       if command:
           if command in self.group:
               #if command but no option then ignore
               if len(self.group[command]) >= 2:
                   #Command group
                   if self.group[command].get('command'):
                       print()
                       sys.stdout.write('Usage: {} {} [OPTION] [<args>]\n'.format(self.program,command))
                       print()
                       if self.group[command].get('desc'):
                           _group_desc=WrapString(self.group[command]['desc'],nspace=short_len+long_len+desc_space)
                           sys.stdout.write(' %s\n'%(_group_desc))
                       sys.stdout.write('\n[OPTION]\n')
                       #Print regular/global option
                       for oo in self.option:
                           print_option(self.option[oo])
                   #normal group
                   else:
                       if self.group[command].get('desc'):
                           sys.stdout.write('%-{}s%s\n'.format(short_len+long_len)%(' * {}'.format(command),_group_desc))
                       else:
                           sys.stdout.write('%-{}s\n'.format(short_len+long_len)%(' * {}'.format(command)))
                   sys.stdout.flush()
                   #Print group/local option
                   for oo in self.group[command]:
                       print_option(self.group[command][oo])
                   #Print other group option
                   if self.group[command].get('command'):
                       for gg in self.group:
                           if not self.group[gg].get('command'):
                               if self.group[gg].get('desc'):
                                   _group_desc=WrapString(self.group[gg]['desc'],nspace=short_len+long_len+desc_space)
                                   sys.stdout.write('\n%-{}s%s\n'.format(short_len+long_len)%(' * {}'.format(gg),_group_desc))
                               else:
                                   sys.stdout.write('\n%-{}s\n'.format(short_len+long_len)%(' * {}'.format(gg)))
                               for oo in self.group[gg]:
                                   print_option(self.group[gg][oo])
                   os._exit(0)
           elif not ignore_unknown_command:
               print('{} not found'.format(command))
               os._exit(1)
       #######################
       #Print Help(Main Design)
       #######################
       #if call or (Short and Short in self.argv) or (Long and Long in self.argv):
       if call or IsSame(Get(self.args,0),Short)  or IsSame(Get(self.args,0),Long):
           if self.cmd_id > 0 and not self.commands:
                sys.stderr.write("ERROR: defined extra command at SysArg(..,cmd_id=N).\nIt required defineing command with SysArg.define(...,group=<cmd name>,command=True)\n")
                sys.stderr.flush()
                os._exit(1)
           #Print Program
           if self.program:
               if self.option:
                   if self.commands:
                       sys.stdout.write('\nUsage: {} <command> [OPTION] [<args>]\n'.format(self.program))
                   else:
                       sys.stdout.write('\nUsage: {} [OPTION] [<args>]\n'.format(self.program))
               else:
                   if self.commands:
                       sys.stdout.write('\nUsage: {} <command> [<args>]\n'.format(self.program))
                   else:
                       sys.stdout.write('\nUsage: {} [<args>]\n'.format(self.program))
               if self.version:
                   sys.stdout.write('Version: {}\n\n'.format(self.version))
               sys.stdout.flush()
           #Print Special Group Option
           if self.commands and self.cmd_id > 0 and len(self.argv) > self.cmd_id and self.argv[self.cmd_id] in self.commands:
               if self.group[self.argv[self.cmd_id]].get('command'):
                   if self.group[self.argv[self.cmd_id]].get('desc'):
                       _group_desc=WrapString(self.group[self.argv[self.cmd_id]]['desc'],nspace=short_len+long_len+desc_space)
                       sys.stdout.write('* %-{}s  %s\n'.format(short_len+long_len-2)%(self.argv[self.cmd_id],_group_desc))
                   else:
                       sys.stdout.write('* %-{}s\n'.format(short_len+long_len-2)%(self.argv[self.cmd_id]))
                   sys.stdout.flush()
               for oo in self.group[self.argv[self.cmd_id]]:
                   print_option(self.group[self.argv[self.cmd_id]][oo])
               os._exit(0)
           #Print Desc
           if self.desc:
               sys.stdout.write(self.desc+'\n')
               sys.stdout.flush()
           force=Variable(self.SysArg_hidden_show,default=False,mode='all')
           #Supported Commands display Description
           if self.commands:
               sys.stdout.write('\nSupported <command>s are:\n')
               for cc in self.commands:
                   if not force and self.group.get(cc,{}).get('hidden'): continue
                   if self.group.get(cc,{}).get('desc') :
                       _group_desc=WrapString(self.group[cc]['desc'],nspace=short_len+long_len+desc_space)
                       if self.group.get(cc,{}).get('arg'): # required argument
                           sys.stdout.write('  %-{}s%s\n'.format(short_len+long_len)%('{} [OPT] <arg>'.format(cc),_group_desc))
                       else:
                           sys.stdout.write('  %-{}s%s\n'.format(short_len+long_len)%(cc,_group_desc))
                   else:
                       sys.stdout.write('  %-{}s\n'.format(short_len+long_len)%(cc))
                   sys.stdout.flush()
               sys.stdout.flush()
           sys.stdout.write('\n[OPTION]\n')
           #Print Help Option
           _help_desc=WrapString(self.help_desc,nspace=short_len+long_len+desc_space)
           if Short and Long:
               sys.stdout.write('%{}s, %-{}s%s\n'.format(short_len,long_len)%(Short,Long,_help_desc))
           elif Long:
               sys.stdout.write('%s  %-{}s%s\n'.format(long_len)%(Space(short_len),Long,_help_desc))
           elif Short and Long:
               sys.stdout.write('%{}s  %s\n'.format(short_len)%(Short,Space(long_len),_help_desc))
           sys.stdout.flush()
           #Print Regular Option
           for oo in self.option:
               print_option(self.option[oo])
           #Print Group Option
           for gg in self.group:
               #if command but no option/hidden then ignore
               group_hidden=self.group[gg].pop('hidden') if 'hidden' in self.group[gg] else None
               if len(self.group[gg]) >= 3 and (not group_hidden or force):
                   print()
                   if self.group[gg].get('desc'):
                       _group_desc=WrapString(self.group[gg]['desc'],nspace=short_len+long_len+desc_space)
                       sys.stdout.write('%-{}s%s\n'.format(short_len+long_len)%(' * {}'.format(gg),_group_desc))
                   else:
                       sys.stdout.write('%-{}s\n'.format(short_len+long_len)%(' * {}'.format(gg)))
                   sys.stdout.flush()
                   for oo in self.group[gg]:
                       print_option(self.group[gg][oo])
           #Print Epilog
           if self.epilog:
               print(self.epilog)
           os._exit(0)
    def Args(self,syms=[]):
        tt=[]
        for ii in self.__dict__.get('args'):
            c=True
            for i in syms:
                if re.search('^{}\w+'.format(i),ii):
                    if ii not in self.argo: self.argo.append(ii)
                    c=False
                    break
            if c: tt.append(ii)
        if tt and tt != self.__dict__.get('args'):
            self.__dict__['args']=tt
        return self.__dict__.get('args')
    def ArgO(self): # Others
        return self.__dict__.get('argo')
    def Opts(self,name=None,get_true=False,combin=False):
        out={}
        o=self.__dict__.get('option',{})
        for i in o:
            if o[i].get('value'):
                if get_true and o[i].get('value') != get_true: continue
                out[o[i].get('short',o[i].get('long'))]=o[i].get('value')
        o=self.__dict__.get('group',{}).get(name,{})
        for i in o:
            if not isinstance(o[i],dict): continue
            if o[i].get('value'):
                if get_true and o[i].get('value') != get_true: continue
                out[o[i].get('short',o[i].get('long'))]=o[i].get('value')
        if combin:
            m=''
            for i in out.keys():
                if len(i) == 2:
                    m=m+i[1:]
            if m: return '-{}'.format(m)
        return out

