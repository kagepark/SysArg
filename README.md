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
pip install SysArg
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
  - type: default str, if you want int value then change to int, wrong type then not taken
  - group: make a special group's prameters
  - group_desc: group desciption
  - command: If Command Group(bool)


