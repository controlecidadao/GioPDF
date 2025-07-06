@echo off
chcp 65001

REM Script para ativar o ambiente virtual giopdf e executar a aplicação Streamlit

set "PATH=%cd%\miniconda3\Scripts;%cd%\miniconda3\condabin;%PATH%"
call "%cd%\miniconda3\Scripts\activate.bat" giopdf

echo.
echo Ambiente 'giopdf' ativado com sucesso
echo Iniciando a aplicação Streamlit...
echo.

REM Abre nova janela CMD, ativa o ambiente e executa o Streamlit
start "GIO PDF" cmd /k streamlit run app.py"

REM Alternativa sem abrir nova janela (descomente se preferir)
REM streamlit run app.py
REM cmd /k