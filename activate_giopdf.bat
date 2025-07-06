@echo off 
REM Script para ativar o ambiente virtual giopdf 
set "PATH=C:\Users\t203771\Documents\GIO_PDF\miniconda3\Scripts;C:\Users\t203771\Documents\GIO_PDF\miniconda3\condabin;%PATH%" 
call "C:\Users\t203771\Documents\GIO_PDF\miniconda3\Scripts\activate.bat" giopdf 
echo. 
echo Ambiente 'giopdf' ativado com sucesso 
echo Para executar a aplicação, use: streamlit run app.py 
echo. 
cmd /k 
