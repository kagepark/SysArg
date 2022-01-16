# SysArg
CLI Argument Parser Functions

## Contents
1. Install
1. Initialize
1. Functions
   1. defind        : Setup option/command/group/help....
   1. Cmd           : Get Inputed Special Command (it need cmd_id=1 parameter at initialize)
   1. Get           : Get parameter's input values
   1. Version       : show version
   1. Check         : Check option 
   1. Help          : Dispaly Help
   

- Install
```javascript
pip3 install SysArg
```

- Initialize
   - program : Program Name
   - cmd_id  : command ID
   - desc    : Program Description
   - epilog  : Program Epilog (tail string of the help)
   - version : define Program version
   - help_desc: Customize description of Help

```javascript
import SysArg
arg=SysArg.SysArg(program='ArgTest',desc='ARG. Testing',version='1.0')
```

if you want make a special command in this application case: (ArgTest command ...)
```javascript
import SysArg
arg=SysArg.SysArg(program='ArgTest',desc='ARG. Testing',version='1.0',cmd_id=1)
```

- defind
  - name: (required) parameter name
  - short: short parameter(-XX)
  - long: long parameter(--XX)
  - params: 
     - default:0(found parameter then True), 
     - 0<n: how many required parameter input data(number)
     - \- : until next parameter or until finished inputs
  - params_name: --abc=<PARAMS_NAME(Explain String)> (this format)
  - required: required parameter (default False, need then True)
  - default: default value when no input
  - type: default str, wrong type then not taken (support: str,int,list,tuple,dict)
     - spliter: if you set list or tuple at type. but input is single string then using spliter (example: , : )
  - group: make a special group's prameters
  - group_desc: group desciption
  - command: If Command Group then True
  - arg: If this group is command and need input argument then True
  - select: If you want selectable input, this is list type format, if wrong input then Get() command will make an error


example format:  -n, --numbre=INT
```javascript
arg.define('number',short='-n',long='--number',params_name='INT',type=int,desc='Number Input')
```

it this option required value
```javascript
arg.define('number',short='-n',long='--number',params_name='INT',type=int,desc='Number Input',required=True)
```

Add some of GROUP(ex: INPUT)
```javascript
arg.define('number',short='-n',long='--number',params_name='INT',type=int,desc='Number Input',group='INPUT')
```

example format:  -n, --numbre INT
```javascript
arg.define('number',short='-n',long='--number',params=1,type=int,desc='Number Input')
```

example format:  -l, --list ['A','B']
```javascript
arg.define('List',short='-l',long='--list',params=1,type=list,desc='List Input')
```

example format:  -l, --list 'A,B,C'
```javascript
arg.define('List',short='-l',long='--list',params=1,type=list,spliter=',',desc='List Input')
```

example format:  -l, --list A B C
```javascript
arg.define('List',short='-l',long='--list',params=3,type=list,desc='List Input')
```

example default : if not input then default get 7
```javascript
arg.define('N',short='-n',long='--number',params=1,type=int,desc='Number Input',default=7)
```

example check parameter: if -n or --number parameter then True
```javascript
arg.define('N',short='-n',long='--number')
```

example command group:
```javascript
arg.define(group_desc='File list',group='ls',command=True)
arg.define('show_detail',short='-l',desc='show detail',group='ls')
arg.define('show_time',short='-t',desc='show time',group='ls')
arg.define('number',short='-n',long='--number',params_name='INT',type=int,desc='Number Input',group='INPUT')
arg.define(group_desc='Power command',group='power',command=True,arg=True,select=['on','off','reset'])
```

- Cmd
Get Input Command name
```javascript
cmd=arg.Cmd()
```

Check input 'command'
```javascript
   if arg.Cmd('command'):
       ~~~~
   else:
       ~~~~
```


- Get parameter's value
   - All data
```javascript
param=arg.Get()
```

   - Get group INPUT's All data
```javascript
param=arg.Get(group='INPUT')
```

   - Get value of COMMAND power's data
```javascript
# ./APP power -i x.x.x.x on
```

```javascript
if arg.Cmd('power'):
    pw_cmd=arg.Get(group='power')
    if pw_cmd == 'on':
        ...
    elif pw_cmd == 'off':
        ...
    ....
```

   - Get Parameter number's data
```javascript
param=arg.Get('number')
```

   - Get Parameter List's data in the INPUT group
```javascript
param=arg.Get('List',group='INPUT')
```


Simple Example)
```javascript
import SysArg
arg=SysArg.SysArg(program='ArgTest',desc='ARG. Testing',version='1.0',cmd_id=1)
arg.define('a',short='-a',long='--abc',desc='test input',params=1)
arg.define(group_desc='test command',group='ls',command=True)
arg.define('detail',short='-l',desc='show detail',group='ls')
arg.define('find_time',short='-t',desc='find time',group='ls',params=1)
arg.Version()
arg.Help()

cmd=arg.Cmd()
a=arg.Get('a')
```
Output:
```
$ python3 a.py --help
Usage: ArgTest <command> [OPTION] [<args>]
Version: 1.0
ARG. Testing

Supported <command>s are:
  ls                                 test command

[OPTION]
   -h, --help                        Help
   -a, --abc                         test input(input(1):S)

* ls                                 test command
   -l                                show detail
   -t                                find time(input(1):S)
```
