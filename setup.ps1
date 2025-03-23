docker compose up postgres adminer -d

conda env create -f environment.yml

conda activate pdf2notes

Set-Location .\scripts\

uvicorn main:app --host 0.0.0.0 --port 6500

conda deactivate