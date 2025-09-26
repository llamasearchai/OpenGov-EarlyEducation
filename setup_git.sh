#!/bin/bash
# Setup Git configuration for OpenEarlyEducation project

# Set up Git user configuration
echo "Setting up Git configuration..."
git config user.name "Nik Jois"
git config user.email "nikjois@llamasearch.ai"

# Set up Git defaults for this project
git config core.editor "nano"
git config core.autocrlf "input"
git config core.safecrlf "warn"

# Set up commit message template
git config commit.template ".git-commit-template"

# Configure default merge strategy
git config pull.rebase false

# Set up helpful aliases
git config alias.co "checkout"
git config alias.br "branch"
git config alias.ci "commit"
git config alias.st "status"
git config alias.unstage "reset HEAD --"
git config alias.last "log -1 HEAD"
git config alias.visual "!gitk"

# Configure push behavior
git config push.default "simple"

# Set up Git LFS if available (for large files)
if command -v git-lfs >/dev/null 2>&1; then
    echo "Git LFS detected, setting up..."
    git lfs track "*.db"
    git lfs track "*.pdf"
    git lfs track "*.zip"
fi

echo "Git configuration complete!"
echo "You can now make your first commit:"
echo "  git add ."
echo "  git commit -m 'Initial commit: Complete OpenEarlyEducation v2.0.0'"
echo ""
echo "To push to your repository:"
echo "  git remote add origin <your-repo-url>"
echo "  git push -u origin main"
