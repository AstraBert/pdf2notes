eval "$(conda shell.bash hook)"

conda activate pdf2notes
cd /app/
uvicorn main:app --host 0.0.0.0 --port 6500
conda deactivate
