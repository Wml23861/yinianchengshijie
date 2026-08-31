@echo off
rem 《心上众生》硬规则自检包装脚本
rem 用法：check.bat <章文件名>
rem 例：check.bat 50_第五十章_无疾而终.md
rem 退出码 0=全过，1=有 [X]，2=文件未找到

"F:\Program Files (x86)\python\python.exe" "e:\心界\yinianchengshijie\novel\工具\硬规则自检.py" %*
exit /b %ERRORLEVEL%
