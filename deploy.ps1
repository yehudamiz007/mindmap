Set-Location 'C:\Users\YEHUDA\.openclaw\workspace'
Copy-Item mindmap.html index.html -Force
git add mindmap.html index.html
git commit -m "mindmap: 3-level hierarchy"
git push origin main
