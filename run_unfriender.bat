:: filepath: c:\Users\Jason\Desktop\psnawp-3.0.0\PSN-Unfriender\run_unfriender.bat
@echo off
echo Installing requirements...
pip install -r requirements.txt
echo.
echo Running unfriender.py...
python gui.py
pause