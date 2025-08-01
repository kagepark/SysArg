import os
import re
import sys
from kmport import *

#redesigned main structure
#version 2.x
#Kage Park

def StdErr(msg,end='\n'):
    sys.stderr.write(f'{msg}{end}')
    sys.stderr.flush()

def StdOut(msg,end='\n'):
    sys.stdout.write(f'{msg}{end}')
    sys.stdout.flush()

class SysArg:
    def __init__(self,*args,**opts):
        self.program=opts.get('program','APP')
        self.desc=opts.get('desc')
        self.version=opts.get('version')
        self.epilog=opts.get('epilog')
        self.support_unknown_option=opts.get('support_unknown',opts.get('support_unknown_option',False))
        self.SysArg_hidden_show=Bool(opts.get('SysArg_hidden_show',False),want=True,auto_bool=True)
        self.help_desc=opts.get('help_desc','Help')
        self.help_tag=opts.get('help_tag',['-h','--help'])
        if not isinstance(self.help_tag,list):
            self.help_tag=[self.help_tag]
        self.version_desc=opts.get('version_desc','Show version')
        self.version_tag=opts.get('version_tag',['-v','--version'])
        if not isinstance(self.version_tag,list):
            self.version_tag=[self.version_tag]
        if not args:
            #Copy original
            self.argv=tuple(sys.argv[:])
            #Copy to work
            self.args=list(sys.argv[:])
        else:
            #Copy original
            self.argv=tuple(args[:])
            #Copy to work
            self.args=list(args[:])

        self.default_command_id=opts.get('default_command_id',self.args.index(self.SelfFilename()))
        self.groups={}
        self.argo=[]
        self.run_command=None

    def SelfFilename(self,path=None):
        if getattr(sys,'frozen',False):
            if path in ['basename','filename']:
                return os.path.basename(sys.executable)
            elif path in ['full','abs','absolut']:
                return sys.executable
        else:
            if path in ['basename','filename']:
                return os.path.basename(__file__)
            elif path in ['full','abs','absolut']:
                return __file__
        return sys.argv[0]

    def SetGroup(self,name,desc=None,idx=None,command=None,hidden=False):
        if name not in self.groups:
            self.groups[name]={}
        self.groups[name]['desc']=desc
        self.groups[name]['hidden']=hidden
        if command:
            self.groups[name]['command']=True
            if not idx:
                self.groups[name]['idx']=self.default_command_id+1
            else:
                self.groups[name]['idx']=idx

    def GetGroupNames(self,command=None,whole=False):
        #command : None: All groups
        #command : True: All commands
        #command : False: All groups exclude commands
        out=[]
        for k in self.groups:
            if isinstance(self.groups[k],dict):
                if command is True:
                    if self.groups[k].get('command'):
                        out.append(k)
                elif command is False:
                    if not self.groups[k].get('command'):
                        out.append(k)
                else:
                    out.append(k)
        if whole:
            if 'global' not in out:
                return [None,'global']+out
            return [None]+out
        else:
            if 'global' in out: out.remove('global')
            return out

    def CheckNameOpts(self,name,short=None,long=None,group=None,command=None,verify=False):
        def _chk_(name,gg,short=None,long=None):
            #Check items in each groups
            if name in self.groups.get(gg,{}):
                return True,(name,self.groups[gg][name].get('short'),self.groups[gg][name].get('long'),gg,1)
            if short:
                if verify and self.IsCombinedOpt(short): ##sys.argv analysis area
                    #return list for combined option
                    #if this short is in combined then adding to combin
                    #if not then normal short
                    opt=[]
                    for k in self.groups.get(gg,{}):
                        if not isinstance(self.groups[gg][k],dict): continue
                        #Check combin
                        if self.groups[gg][k]['combin']:
                            if self.groups[gg][k]['short'][-1] in short[1:]: #current combined parameter is in inputs(sys.argv) combined parameter
                                if (k,self.groups[gg][k].get('short'),self.groups[gg][k].get('long'),gg,2) not in opt:
                                    opt.append((k,self.groups[gg][k].get('short'),self.groups[gg][k].get('long'),gg,2))
                        else:
                            #if the condition is not combin then returh tuple
                            if self.groups[gg][k]['short'] == short:
                                return True,(k,self.groups[gg][k].get('short'),self.groups[gg][k].get('long'),gg,2)
                    if opt:
                        return True,opt
                    else:
                        if not long:
                            return False,[(None,None,None,None,None)]
                else: # define and other check
                    #return tuple for single option
                    for k in self.groups.get(gg,{}):
                        if not isinstance(self.groups[gg][k],dict): continue
                        if self.groups[gg][k]['short'] == short:
                            return True,(k,self.groups[gg][k].get('short'),self.groups[gg][k].get('long'),gg,2)
            if long:
                for k in self.groups.get(gg,{}):
                    if not isinstance(self.groups[gg][k],dict): continue
                    if self.groups[gg][k]['long'] == long:
                        return True,(k,self.groups[gg][k].get('short'),self.groups[gg][k].get('long'),gg,3)
            return False,(None,None,None,None,None)

        def _globals_(name,short=None,long=None):
            # global > global group > command
            #if no group then check duplicated parameter in (inside) global 
            if verify: #sys.argv analysis area
                oo=[]
                ok=False
                for gg in self.GetGroupNames(command=False,whole=True): #Globals search all groups
                    o=_chk_(name,gg,short,long)
                    if o[0]:
                        if o[1] in oo: continue
                        ok=True
                        if isinstance(o[1],list): #combined option
                            oo=oo+o[1]
                        else: # normal option
                            oo=o[1]
                if ok:
                    return ok,oo
            else: # define and other check
                for gg in ['global']+self.GetGroupNames(command=False): #Globals search all groups
                    o=_chk_(name,gg,short,long)
                    if o[0]:
                        return o
            return False,(None,None,None,None,None)

        def _commands_(name,short=None,long=None,group=None):
            #if have a group then check duplicated parameter in (inside) group
            global_group=self.GetGroupNames(command=False,whole=True) #Globals search all groups
            if verify: #sys.argv analysis area
                oo=[]
                ok=False
                for gg in global_group: # Global without command options
                    o=_chk_(name,gg,short,long)
                    if o[0]:
                        if o[1] in oo: continue
                        ok=True
                        if isinstance(o[1],list): #combined option
                            oo=oo+o[1]
                        else: #normal option
                            oo=o[1]
                if group not in global_group: # Command options
                    a=_chk_(name,group,short,long)
                    if a[0]:
                        ok=True
                        if isinstance(o[1],list): #combined option
                            oo=oo+a[1]
                        else: # normal option
                            oo=a[1]
                if ok:
                    return ok,oo
            else: #define and other check
                for gg in global_group:
                    o=_chk_(name,gg,short,long)
                    if o[0]:
                        return o
                if group not in global_group:
                    return _chk_(name,group,short,long)
            return False,(None,None,None,None,None)
        if not group:
            group='global'
        global_group=self.GetGroupNames(command=False,whole=True) #Globals search all groups
        if group not in global_group and command: # For command
            return _commands_(name,short,long,group)
        else:
            return _globals_(name,short,long)

    def Define(self,name,group=None,**opts):
        #Menu define
        def _define_(name,group,**opts):
            sub_group_template={'short':None,
                                'long':None,
                                'params':0,
                                'params_name':None,
                                'type':str,
                                'desc':None,
                                'required':False,
                                'default':None,
                                'spliter':None,
                                'select':None,
                                'combin':False,
                                'hidden':False,
                                'value':None
                                }

            if not group:
                if 'global' not in self.groups:
                    self.groups['global']={}
                GroupCfg=self.groups['global']
            elif group in self.groups:
                GroupCfg=self.groups[group]
            else:
                StdErr(f"Please define command '{group}' first before define {name} at group='{group}'")
                os._exit(1)
            found=self.CheckNameOpts(name,short=opts.get('short'),long=opts.get('long'),group=group,command=GroupCfg.get('command'))
            if found[0]:
                fp=found[1]
                StdErr(f"Duble defined '{fp[1]}' in {group}({name}:{opts.get('short')}:{opts.get('long')}) and {fp[-2]}({fp[0]}:{fp[1]}:{fp[2]})\n(Can not duplicate options between Global and sub-command)")
                os._exit(1)

            # inside command define
            if 'combin' not in GroupCfg:
                GroupCfg['combin']=[]
            for k in opts:
                if k in sub_group_template:
                    sub_group_template[k]=opts[k]
                    if k == 'combin' and opts[k] is True:
                        _short=opts.get('short')
                        if isinstance(_short,str) and len(_short) == 2 and _short[0] == '-' and _short[1].isalnum():
                            if _short[1] not in GroupCfg['combin']:
                                GroupCfg['combin'].append(_short[1])
                        else:
                            StdErr('combin required _short parameter with single character with - (ex: -a)')
                            os._exit(1)
            #if exist params_name then change params to default 1
            if opts.get('params_name') and not opts.get('params'):
                sub_group_template['params']=1

            #Add default value at value and type
            default_value=opts.get('default')
            if default_value:
                default_type=type(default_value).__name__
                sub_group_template['value']=default_value
                if default_type == 'list':
                    sub_group_template['type']=list
                elif default_type == 'tuple':
                    sub_group_template['type']=tuple
                elif default_type == 'dict':
                    sub_group_template['type']=dict
                elif default_type == 'int':
                    sub_group_template['type']=int
                elif default_type == 'float':
                    sub_group_template['type']=float
                elif default_type == 'bool':
                    sub_group_template['type']=bool
                elif default_type == 'str':
                    if IpV4(default_value):
                        sub_group_template['type']='ip'
                    elif MacV4(default_value):
                        sub_group_template['type']='mac'
                    else:
                        sub_group_template['type']=str
                if default_type != 'bool' and sub_group_template['params'] == 0:
                    sub_group_template['params']=1
            #Setup params=0 then change type to bool
            if sub_group_template.get('params') == 0:
                sub_group_template['type']=bool
            GroupCfg[name]=sub_group_template

        if opts.get('command'): # group for command
            self.SetGroup(name if name else group,desc=opts.get('desc'),command=True,hidden=opts.get('hidden'))
        elif group not in self.groups: #group for not command
            self.SetGroup(group,desc=opts.get('desc'),command=opts.get('command'),hidden=opts.get('hidden'))
        if not opts.get('command'): # define
            _define_(name,group,**opts)

    def IsOpt(self,src):
        #Check option : example) -X, --X
        if isinstance(src,str):
            if src.startswith('-'):
                if len(src) == 2:
                    #if src[1].isalpha():
                    if src[1].isalnum():
                        return True
                elif len(src) > 2:
                    #if src[1] == '-' and src[1].isalpha():
                    if src[1] == '-' and src[2].isalnum():
                        return True
                    #elif src[1].isalpha():
                    elif src[1].isalnum():
                        return True
        return False

    def GetCombinedOpt(self,src):
        O=[]
        if self.IsOpt(src):
            if src[0] == '-' and src[1].isalnum():
                for i in src[1:]:
                    O.append(f"-{i}")
        return O

    def IsCombinedOpt(self,src):
        O=[]
        if self.IsOpt(src):
            if src[0] == '-' and src[1].isalnum() and len(src[1:]) > 1:
                return True
        return False

    def GetGroupParameters(self,name=None):
        #Get Whole group db
        out={}
        if not name: name='global'
        if name in self.groups:
            for k in self.groups[name]:
                if isinstance(self.groups[name][k],dict):
                    out[k]=self.groups[name][k].get('value')
        else:
            StdErr(f"Can not find groupname '{name}'")
            os._exit(1)
        return out

    def Get(self,name=None,group=None):
        group_data=self.GetGroupParameters(group)
        if name:
            return group_data.get(name)
        return group_data

    def Cmd(self,name=None):
        if name:
            return self.run_command == name

        if self.run_command: return self.run_command
        #Get support command list
        # Find current running command
        for c in self.GetGroupNames(command=True):
            idx=Int(self.groups[c].get('idx'))
            if IsInt(idx) and len(self.argv) > idx and self.argv[idx] == c: #command
                self.run_command=c
                return self.run_command

    def GetCmdID(self,name):
        for c in self.GetGroupNames(command=True):
            idx=Int(self.groups[c].get('idx'))
            if IsInt(idx) and len(self.argv) > idx and self.argv[idx] == c: #command
                return idx

    # Aanalysis sys.argv : fill up from sys.argv to parameters
    def Initialize(self):
        def _analysis_params_(c,args):
            i=0
            while i < len(args):
                #Single parameter
                if self.IsOpt(args[i]):
                    #Version
                    if args[i] in self.version_tag:
                        if i == 0 or args[0] == self.Cmd():
                            #own version or my group's version
                            StdOut(self.version)
                            os._exit(0)
                        elif not self.Cmd():
                            #external sub-command's version then return to sub-command's version
                            return
                    #Help
                    elif args[i] in self.help_tag:
                        if i == 0 or args[0] == self.Cmd():
                            #own help or my group's help
                            self.Help()
                            os._exit(0)
                        elif not self.Cmd():
                             #external sub-command's help then return to sub-command's help
                            return
                    #Todo:
                    # check combined options condition
                    # then split it to single
                    # and try below code to each other with combin tag for only search for combined single tag
                    # if not found then put the whole tag to without combined to short
                    # ether one can find

                    #Other user defined options
                    ok,found=self.CheckNameOpts(None,short=args[i],long=args[i],group=c,command=True,verify=True)
                    found_tag=args[i]
                    if ok:
                        #For combined options, combined option must be bool without input value
                        if isinstance(found,list):
                            for x in found:
                                cg=x[-2]
                                found_type=self.groups[cg][x[0]].get('type')
                                req_data_num=self.groups[cg][x[0]].get('params')
                                if found_type is bool and req_data_num == 0:
                                    self.groups[cg][x[0]]['value']=True
                                else:
                                    StdErr(f"Something wrong for combined option at {x[0]}:type({found_type}),params({req_data_num}) group={cg}.\nPlease check it. it should be type=bool, params=0")
                                    os._exit(1)
                        else:
                            #Normal option
                            cg=found[-2]
                            found_type=self.groups[cg][found[0]].get('type')
                            req_data_num=self.groups[cg][found[0]].get('params')
                            #BOOL
                            if found_type is bool:
                                if req_data_num == 0:
                                    self.groups[cg][found[0]]['value']=True
                                elif len(args) >= i+1 and not self.IsOpt(args[i+1]):
                                    try:
                                        if args[i+1].lower() == 'true':
                                            self.groups[cg][found[0]]['value']=True
                                        elif args[i+1].lower() == 'false':
                                            self.groups[cg][found[0]]['value']=False
                                        else:
                                            StdErr(f"{args[i+1]} is not bool type, {found_tag}'s type required bool")
                                            os._exit(1)
                                    except:
                                        StdErr(f"{args[i+1]} is not bool type, {found_tag}'s type required bool")
                                        os._exit(1)
                     
                            elif found_type in [int,float]:
                                if len(args) > i+1 and not self.IsOpt(args[i+1]):
                                    i+=1
                                    if found_type is float:
                                        try:
                                            self.groups[cg][found[0]]['value']=float(args[i])
                                        except:
                                            StdErr(f"{args[i]} is not float type, {found_tag}'s type required float")
                                            os._exit(1)
                                    else:
                                        try:
                                            self.groups[cg][found[0]]['value']=int(args[i])
                                        except:
                                            StdErr(f"{args[i]} is not int type, {found_tag}'s type required int")
                                            os._exit(1)
                                else:
                                    StdErr(f"{found_tag} required int value. missing value")
                                    os._exit(1)
                            elif found_type in [list,tuple]:
                                spliter=self.groups[cg][found[0]].get('spliter')
                                if len(args) > i+req_data_num:
                                    v=[]
                                    if req_data_num == 1:
                                        i+=1
                                        if self.IsOpt(args[i]):
                                            StdErr(f"{args[i]} is not value, {found_tag} required {req_data_num} values in {cg}")
                                            os._exit(1)
                                        if spliter:
                                            v=args[i].split(spliter)
                                        else:
                                            v=[args[i]]
                                    else:
                                        for x in range(1,req_data_num+1):
                                            i+=1
                                            if self.IsOpt(args[i]):
                                                StdErr(f"{args[i]} is not value, {found_tag} required {req_data_num} values in {cg}")
                                                os._exit(1)
                                            v.append(args[i])
                                    if found_type is tuple:
                                        self.groups[cg][found[0]]['value']=tuple(v)
                                    else:
                                        self.groups[cg][found[0]]['value']=v
                            elif isinstance(found_type,str):
                                found_type=found_type.lower()
                                if found_type == 'ip':
                                    if len(args)<= i+1 or self.IsOpt(args[i+1]):
                                        StdErr(f"{args[i]} is not value, {found_tag} required 1 values in {cg}")
                                        os._exit(1)
                                    i+=1
                                    ip=IpV4(args[i])
                                    if ip:
                                        self.groups[cg][found[0]]['value']=ip
                                    else:
                                        StdErr(f"{found_tag} required ip format")
                                        os._exit(1)
                                elif found_type == 'mac':
                                    if len(args) <= i+1 or self.IsOpt(args[i+1]):
                                        StdErr(f"{args[i]} is not value, {found_tag} required 1 values in {cg}")
                                        os._exit(1)
                                    i+=1
                                    mac=MacV4(args[i])
                                    if mac:
                                        self.groups[cg][found[0]]['value']=mac
                                    else:
                                        StdErr(f"{found_tag} required MAC format")
                                        os._exit(1)
                                else: #auto matic convert : found_type in ['auto']:
                                    spliter=self.groups[cg][found[0]].get('spliter')
                                    if len(args) > i+req_data_num:
                                        v=[]
                                        if req_data_num == 1:
                                            i+=1
                                            if self.IsOpt(args[i]):
                                                StdErr(f"{args[i]} is not value, {found_tag} required {req_data_num} values in {cg}")
                                                os._exit(1)
                                            if spliter:
                                                for x in args[i].split(spliter):
                                                    try:
                                                        v.append(eval(x))
                                                    except:
                                                        v.append(x)
                                            else:
                                                try:
                                                    v=[eval(args[i])]
                                                except:
                                                    v=[args[i]]
                                        else:
                                            for x in range(1,req_data_num+1):
                                                i+=1
                                                if self.IsOpt(args[i]):
                                                    StdErr(f"{args[i]} is not value, {found_tag} required {req_data_num} values in {cg}")
                                                    os._exit(1)
                                                try:
                                                    v.append(eval(args[i]))
                                                except:
                                                    v.append(args[i])
                                        self.groups[cg][found[0]]['value']=v
                            elif type(found_type).__name__ in ['function','method']:
                                if len(args) > i+req_data_num:
                                    v=[]
                                    for x in range(1,req_data_num+1):
                                        i+=1
                                        if self.IsOpt(args[i]):
                                            StdErr(f"{args[i]} is not value, {found_tag} required {req_data_num} values in {cg}")
                                            os._exit(1)
                                        v.append(args[i])
                                    o=found_type(*v)
                                    if isinstance(o,tuple):
                                        if isinstance(o[0],bool):
                                            if o[0]:
                                                self.groups[cg][found[0]]['value']=o[1:]
                                            else:
                                                StdErr(f"{v} is not right value of {found_tag}, issue with {o[1:]}")
                                                os._exit(1)
                                        else:
                                            self.groups[cg][found[0]]['value']=o
                                    else:
                                        self.groups[cg][found[0]]['value']=o
                            else:
                                if len(args) > i+req_data_num:
                                    v=[]
                                    for x in range(1,req_data_num+1):
                                        i+=1
                                        if self.IsOpt(args[i]):
                                            StdErr(f"{args[i]} is not value, {found_tag} required {req_data_num} values in {cg}")
                                            os._exit(1)
                                        v.append(args[i])
                                    self.groups[cg][found[0]]['value']=' '.join(v)
                    else:
                        #this option is not in global group then Error to unknown option
                        #if this option in sub-command's option then it should be check in the sub-command only
                        if c not in self.GetGroupNames(command=False,whole=True): #Globals search all groups
                            if not self.support_unknown_option:
                                StdErr(f"Unknown '{args[i]}'")
                                os._exit(1)
                i+=1

        #Get support command list
        cmds=self.GetGroupNames(command=True)
        run_cmd=self.Cmd()
        ## Find current running command
        #for c in cmds:
        #    idx=Int(self.groups[c].get('idx'))
        #    if IsInt(idx) and len(self.args) > idx and self.args[idx] == c: #command
        #        self.run_cmd=self.args[idx]
        #        break
        #Check global parameters
        args=self.args[1:]
        _analysis_params_('global',self.args[1:])
        #Check required parameters are missing in global options
        for k in self.groups.get('global',{}):
            if not isinstance(self.groups['global'][k],dict): continue
            #Todo:
            #if run this command then required value
            if self.groups['global'][k].get('required') is True or  \
               self.groups['global'][k].get('required') == run_cmd:
                if self.groups['global'][k]['value'] is None:
                    found_tag=self.groups['global'][k].get('short') if self.groups['global'][k].get('short') else self.groups['global'][k].get('long')
                    req_group='global' if self.groups['global'][k].get('required') is True else run_cmd
                    StdErr(f"{found_tag} required values in {req_group}, but missing data")
                    os._exit(1)

        #Global groups parameters
        groups=self.GetGroupNames(command=False)
        # defined commands
        for c in groups:
            _analysis_params_(c,self.args[1:])
            #Check required parameters are missing in command
            for k in self.groups[c]:
                if not isinstance(self.groups[c][k],dict): continue
                if self.groups[c][k].get('required') is True or \
                   self.groups[c][k].get('required') == run_cmd:
                    if self.groups[c][k]['value'] is None:
                        found_tag=self.groups[c][k].get('short') if self.groups[c][k].get('short') else self.groups[c][k].get('long')
                        req_group=c if self.groups[c][k].get('required') is True else run_cmd
                        StdErr(f"{found_tag} required values in {req_group}, but missing data")
                        os._exit(1)

        #Each defined command's parameters
        # defined commands
        for c in cmds:
            idx=self.groups[c]['idx']
            if len(self.args) > idx and self.args[idx] == c: #command
                i=0
                args=self.args[idx+1:]
                _analysis_params_(c,args)

            #Check required parameters are missing in command
            for k in self.groups[c]:
                if not isinstance(self.groups[c][k],dict): continue
                if self.groups[c][k].get('required') is True or \
                   self.groups[c][k].get('required') == run_cmd:
                    if self.groups[c][k]['value'] is None:
                        found_tag=self.groups[c][k].get('short') if self.groups[c][k].get('short') else self.groups[c][k].get('long')
                        req_group=c if self.groups[c][k].get('required') is True else run_cmd
                        StdErr(f"{found_tag} required values in {req_group}, but missing data")
                        os._exit(1)
        # Find Others after parameters
        i=len(args)-1
        while i >= 0:
            if self.IsOpt(args[i]): #Search parameter name to backward
                ok,found=self.CheckNameOpts(None,short=args[i],long=args[i],group='global')
                if ok:
                    n=self.groups[found[-2]][found[0]].get('params')
                    self.argo=args[i+n+1:]
                    return
                # defined commands
                for c in self.GetGroupNames():
                    ok,found=self.CheckNameOpts(None,short=args[i],long=args[i],group=c)
                    if ok:
                        n=self.groups[c][found[0]].get('params')
                        self.argo=args[i+n+1:]
                        return
            i-=1
        if not self.argo:
            self.argo=args[:]

    def GetCommandOptions(self,cmd=None,cmd_line=False):
        #Get current command's all options
        out={}
        #Global Options
        for kk in self.groups.get('global',{}):
            if not isinstance(self.groups['global'][kk],dict): continue
            key=self.groups['global'][kk].get('short',self.groups['global'][kk].get('long'))
            if key:
                out[key]=self.groups['global'][kk].get('value')
        #Global Group Options
        global_group_options=self.GetGroupNames(command=False)
        if global_group_options:
            for gg in global_group_options:
                for kk in self.groups[gg]:
                    if not isinstance(self.groups[gg][kk],dict): continue
                    key=self.groups[gg][kk].get('short',self.groups[gg][kk].get('long'))
                    if key:
                        out[key]=self.groups[gg][kk].get('value')
        #Command Options
        if cmd and cmd in self.groups:
            for kk in self.groups[cmd]:
                if not isinstance(self.groups[cmd][kk],dict): continue
                key=self.groups[cmd][kk].get('short',self.groups[cmd][kk].get('long'))
                if key:
                    out[key]=self.groups[cmd][kk].get('value')
        if cmd_line:
            out_str=''
            for k in out:
                if out[k]:
                    if out_str:
                        if type(out[k]).__name__ == 'bool':
                            out_str=out_str+f' {k}'
                        else:
                            out_str=out_str+f' {k} {out[k]}'
                    else:
                        if type(out[k]).__name__ == 'bool':
                            out_str=f'{k}'
                        else:
                            out_str=f'{k} {out[k]}'
            return out_str
        return out

    def GetCommandOptionValue(self,option=None,cmd=None,parameter_name=None,default=False):
        #Similar Get()
        #But, it searching option's value in global and global group and my command
        #It get options value in whole available group of my command 
        #same as collecting rule with GetCommandOptions

        if not option and not parameter_name:
            return default

        #Global Options
        for kk in self.groups.get('global',{}):
            if not isinstance(self.groups['global'][kk],dict): continue
            if (parameter_name and kk == parameter_name) or \
               (option and (self.groups['global'][kk].get('short') == option or \
               self.groups['global'][kk].get('long') == option)):
                return self.groups['global'][kk].get('value')

        #Global Group Options
        global_group_options=self.GetGroupNames(command=False)
        if global_group_options:
            for gg in global_group_options:
                for kk in self.groups[gg]:
                    if not isinstance(self.groups[gg][kk],dict): continue
                    if (parameter_name and kk == parameter_name) or \
                       (option and (self.groups[gg][kk].get('short') == option or \
                          self.groups[gg][kk].get('long') == option)):
                           return self.groups[gg][kk].get('value')

        #Command Options
        if cmd and cmd in self.groups:
            for kk in self.groups[cmd]:
                if not isinstance(self.groups[cmd][kk],dict): continue
                if (parameter_name and kk == paramter_name) or \
                   (option and (self.groups[cmd][kk].get('short') == option or \
                      self.groups[cmd][kk].get('long') == option)):
                       return self.groups[cmd][kk].get('value')
        return default

    def ArgO(self,filter_option=False): # Others
        if filter_option:
            i=len(self.argo)-1
            while i >= 0:
                if self.IsOpt(self.argo[i]):
                    return self.argo[i+1:]
                i-=1
        #Default return of remained string after filter out defined/required options
        return self.argo

    def Args(self,syms=[]):
        #Todo:
        #Just copy it from old code
        #Why it need it?
        #For what?
        tt=[]
        for ii in self.argv:
            c=True
            for i in syms:
                if re.search('^{}\w+'.format(i),ii):
                    if ii not in self.argo: self.argo.append(ii)
                    c=False
                    break
            if c: tt.append(ii)
        if tt and tt != self.args:
            self.args=tt
        return self.args

    def Help(self,short_len=5,long_len=30,desc_space=2,ignore_unknown_command=False):
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
               return WrapString(_desc,nspace=nspace,auto_tap=True)
           return ''
       #######################
       #Option Design
       #######################
       def print_option(data):
           if isinstance(data,dict):
               if not self.SysArg_hidden_show and data.get('hidden'): return
               _desc=mk_desc(data.get('desc'),default=data.get('default'),required=data.get('required'),nspace=short_len+long_len+desc_space,_type=data.get('type'),_params=data.get('params'),_params_name=data.get('params_name'),_spliter=data.get('spliter'),_select=data.get('select'))
               if data.get('short') and data.get('long'):
                   if len(data.get('short')) > short_len:
                       sss=long_len-(len(data.get('short'))-short_len)
                   else:
                       sss=long_len
                   if data.get('params_name'):
                       StdOut('%{}s, %-{}s%s'.format(short_len,sss)%(data.get('short'),'{}={}'.format(data.get('long'),data.get('params_name')),_desc))
                   else:
                       StdOut('%{}s, %-{}s%s'.format(short_len,sss)%(data.get('short'),data.get('long'),_desc))
               elif data.get('short'):
                   if len(data.get('short')) > short_len:
                       sss=long_len-(len(data.get('short'))-short_len)
                   else:
                       sss=long_len
                   StdOut('%{}s  %s%s'.format(short_len)%(data.get('short'),Space(sss),_desc))
               elif data.get('long'):
                   if data.get('params_name'):
                       StdOut('%s  %-{}s%s'.format(long_len)%(Space(short_len),'{}={}'.format(data.get('long'),data.get('params_name')),_desc))
                   else:
                       StdOut('%s  %-{}s%s'.format(long_len)%(Space(short_len),data.get('long'),_desc))
       # If exist command then print help for the command only (show all)
       command=self.Cmd()
       if command:
           #Command group
           StdOut('')
           StdOut('Usage: {} {} [OPTION] [<args>]'.format(self.program,command))
           StdOut('')
           if self.groups[command].get('desc'):
               _group_desc=WrapString(self.groups[command]['desc'],nspace=short_len+long_len+desc_space,auto_tap=True)
               StdOut(' %s'%(_group_desc))
           StdOut('\n[OPTION]')
           #Print Help Option
           _help_desc=WrapString(self.help_desc,nspace=short_len+long_len+desc_space,auto_tap=True)
           if self.help_tag:
               if len(self.help_tag) == 2:
                   StdOut('%{}s, %-{}s%s'.format(short_len,long_len)%(self.help_tag[0],self.help_tag[1],_help_desc))
               else:
                   if self.help_tag[0][1] == '-':
                       StdOut('%s  %-{}s%s'.format(long_len)%(Space(short_len),self.help_tag[0],_help_desc))
                   else:
                       StdOut('%{}s  %s'.format(short_len)%(self.help_tag[0],Space(long_len),_help_desc))
           #Print global's options
           for ii in self.groups.get('global',{}):
               print_option(self.groups['global'][ii])

           #Print command's regular options
           for oo in self.groups[command]:
               if not isinstance(self.groups[command][oo],dict): continue
               print_option(self.groups[command][oo])

           #Print Global Group Options
           #------------------------------------------------------------------------------------------
           global_group_options=self.GetGroupNames(command=False)
           if global_group_options:
               StdOut('\n[Global Group Options]')
               for gg in global_group_options:
                   #if command but no option/hidden then ignore
                   group_hidden=self.groups[gg].pop('hidden') if 'hidden' in self.groups[gg] else None
                   if len(self.groups[gg]) >= 3 and (not group_hidden or self.SysArg_hidden_show):
                       tt_str='( {} )'.format(gg)
                       StdOut('')
                       __group_desc=self.groups[gg].get('desc') if self.groups[gg].get('desc') else 'group name'
                       _group_desc=WrapString(__group_desc,nspace=short_len+long_len+desc_space,auto_tap=True)
                       StdOut('%-{}s%s'.format(short_len+long_len)%(tt_str,_group_desc))
                       for oo in self.groups[gg]:
                           print_option(self.groups[gg][oo])
               StdOut('')
           os._exit(0)
       #######################
       #Print Help(Main Design)
       #######################
       #Print Program
       commands=self.GetGroupNames(command=True)
       groups=self.GetGroupNames(command=False)
       if self.program:
           if commands:
               StdOut('\nUsage: {} <command> [OPTION] [<args>]'.format(self.program))
           else:
               StdOut('\nUsage: {} [OPTION] [<args>]'.format(self.program))
           if self.version:
               StdOut('Version: {}\n'.format(self.version))

       #Print Desc
       if self.desc:
           StdOut(self.desc)

       #Supported Commands display Description
       if commands:
           StdOut('\nSupported <command>s are:')
           for cc in commands:
               if not self.SysArg_hidden_show and self.groups.get(cc,{}).get('hidden'): continue
               if self.groups.get(cc,{}).get('desc') :
                   _group_desc=WrapString(self.groups[cc]['desc'],nspace=short_len+long_len+desc_space,auto_tap=True)
                   if self.groups.get(cc,{}).get('arg'): # required argument
                       StdOut('  %-{}s%s'.format(short_len+long_len)%('{} [OPT] <arg>'.format(cc),_group_desc))
                   else:
                       StdOut('  %-{}s%s'.format(short_len+long_len)%(cc,_group_desc))
               else:
                   StdOut('  %-{}s'.format(short_len+long_len)%(cc))

       StdOut('\n[OPTION]')
       #Print Help/Version Option
       #------------------------------------------------------------------------------------------
       _help_desc=WrapString(self.help_desc,nspace=short_len+long_len+desc_space,auto_tap=True)
       if len(self.help_tag) == 2:
           StdOut('%{}s, %-{}s%s'.format(short_len,long_len)%(self.help_tag[0],self.help_tag[1],_help_desc))
       else:
           if self.help_tag[0][1] == '-':
               StdOut('%s  %-{}s%s'.format(long_len)%(Space(short_len),self.help_tag[0],_help_desc))
           else:
               StdOut('%{}s  %s'.format(short_len)%(self.help_tag[0],Space(long_len),_help_desc))
       #------------------------------------------------------------------------------------------
       _version_desc=WrapString(self.version_desc,nspace=short_len+long_len+desc_space,auto_tap=True)
       if len(self.version_tag) == 2:
           StdOut('%{}s, %-{}s%s'.format(short_len,long_len)%(self.version_tag[0],self.version_tag[1],_version_desc))
       else:
           if self.version_tag[0][1] == '-':
               StdOut('%s  %-{}s%s'.format(long_len)%(Space(short_len),self.version_tag[0],_version_desc))
           else:
               StdOut('%{}s  %s'.format(short_len)%(self.version_tag[0],Space(long_len),_version_desc))
       #------------------------------------------------------------------------------------------

       #Print Global Options
       #------------------------------------------------------------------------------------------
       for ii in self.groups.get('global',{}):
           print_option(self.groups['global'][ii])
       #------------------------------------------------------------------------------------------

       #Print Global Group Options
       #------------------------------------------------------------------------------------------
       global_group_options=self.GetGroupNames(command=False)
       if global_group_options:
           StdOut('\n[Global Group Options]')
           for gg in global_group_options:
               #if command but no option/hidden then ignore
               group_hidden=self.groups[gg].pop('hidden') if 'hidden' in self.groups[gg] else None
               if len(self.groups[gg]) >= 3 and (not group_hidden or self.SysArg_hidden_show):
                   tt_str='( {} )'.format(gg)
                   StdOut('')
                   __group_desc=self.groups[gg].get('desc') if self.groups[gg].get('desc') else 'group name'
                   _group_desc=WrapString(__group_desc,nspace=short_len+long_len+desc_space,auto_tap=True)
                   StdOut('%-{}s%s'.format(short_len+long_len)%(tt_str,_group_desc))
                   for oo in self.groups[gg]:
                       print_option(self.groups[gg][oo])
       #------------------------------------------------------------------------------------------

       #Print All Commands options
       #------------------------------------------------------------------------------------------
       sub_commands=self.GetGroupNames(command=True)
       if sub_commands:
           StdOut('\n[sub-commands]')
           for gg in sub_commands:
               #if command but no option/hidden then ignore
               group_hidden=self.groups[gg].pop('hidden') if 'hidden' in self.groups[gg] else None
               if len(self.groups[gg]) >= 3 and (not group_hidden or self.SysArg_hidden_show):
                   tt_str=' * {}'.format(gg)
                   StdOut('')
                   if self.groups[gg].get('desc'):
                       _group_desc=WrapString(self.groups[gg]['desc'],nspace=short_len+long_len+desc_space,auto_tap=True)
                       StdOut('%-{}s%s'.format(short_len+long_len)%(tt_str,_group_desc))
                   else:
                       StdOut('%-{}s'.format(short_len+long_len)%(tt_str))
                   for oo in self.groups[gg]:
                       print_option(self.groups[gg][oo])
       #------------------------------------------------------------------------------------------

       #Print Epilog
       #------------------------------------------------------------------------------------------
       if self.epilog:
           StdOut(self.epilog)
       #------------------------------------------------------------------------------------------
       os._exit(0)

    def define(self,name,group=None,**opts):
        #For support Old version
        self.Define(name,group=group,**opts)
