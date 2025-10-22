@echo off
REM GitHub Setup Script for GamifyLearn (Windows)
REM Run this after Git is installed

echo 🚀 Setting up GitHub repository for GamifyLearn...
echo ==================================================

REM Check if git is available
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Git is not installed. Please install Git first.
    echo    Windows: winget install --id Git.Git
    echo    Or download from: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo ✅ Git is installed

REM Initialize git repository
echo 📁 Initializing Git repository...
git init

REM Add all files
echo 📦 Adding all project files...
git add .

REM Create initial commit
echo 💾 Creating initial commit...
git commit -m "Initial commit: GamifyLearn Q-Learning Quiz Platform

🎯 Features:
- Adaptive Q-Learning algorithm with 14-dimensional state space
- Complete gamification system (Beginner → Expert levels)
- Comprehensive analytics with 9 log types
- Modern responsive UI with neon-matte theme
- Real-time performance monitoring
- Historical data: 344+ analytics entries

🚀 Ready for expert testing and production deployment!"

echo.
echo 🔧 Git Configuration:
echo Please set up your GitHub credentials:
echo git config --global user.name "Your Name"
echo git config --global user.email "your.email@example.com"

echo.
echo 📋 Next Steps:
echo 1. Create a new repository on GitHub ^(github.com/new^)
echo 2. Copy the repository URL
echo 3. Run: git remote add origin ^<your-repo-url^>
echo 4. Run: git push -u origin master

echo.
echo 🎉 Your project will then be live on GitHub!
echo.
echo 📚 Repository should include:
echo    ✅ Complete Q-Learning implementation
echo    ✅ User manual and testing checklist
echo    ✅ Comprehensive documentation
echo    ✅ Professional README with badges
echo    ✅ Production-ready code

echo.
echo 🔗 After GitHub setup, share your repository link!
echo    Perfect for showcasing to experts and collaborators.

echo.
echo Press any key to continue...
pause >nul
