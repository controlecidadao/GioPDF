@echo off 
REM Script para ativar o ambiente virtual giopdf 
set "PATH=%cd%\miniconda3\Scripts;%cd%\miniconda3\condabin;%PATH%" 
call "%cd%\miniconda3\Scripts\activate.bat" giopdf 
echo. 
echo Ambiente 'giopdf' ativado com sucesso 
echo Para executar a aplicação, use: streamlit run app.py 
echo. 
cmd /k 
