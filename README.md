# SysArg
CLI Argument Parser Functions


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
