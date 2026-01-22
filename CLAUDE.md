# CLAUDE.md - AI Assistant Guide

## Repository Overview

**Repository**: `arcidiaconom.github.io`
**Type**: GitHub Pages Personal Site
**Purpose**: Static website hosting via GitHub Pages
**Last Updated**: 2026-01-22

This is a GitHub Pages repository that serves as a personal website hosted at `https://arcidiaconom.github.io`. GitHub Pages automatically publishes content from this repository to the web.

## Current Repository Structure

```
arcidiaconom.github.io/
├── README.md                       # Repository description
├── Slides-EndOfSchoolTrip.pdf     # PDF document
└── CLAUDE.md                       # This file - AI assistant guide
```

### File Descriptions

- **README.md**: Basic repository identifier
- **Slides-EndOfSchoolTrip.pdf**: Presentation document (4.4 MB)
- **CLAUDE.md**: This documentation file for AI assistants

## Repository Characteristics

### Current State
- **Minimal Setup**: Repository is in early stages with minimal content
- **No HTML/CSS/JS**: No web pages currently exist
- **No Build System**: No package.json, no build tools configured
- **No Web Framework**: No Jekyll, Hugo, or other static site generators
- **Simple Structure**: Direct file hosting approach

### GitHub Pages Configuration
- **Publishing Source**: Default branch (likely main/master)
- **Custom Domain**: Not configured (uses github.io subdomain)
- **Theme**: No Jekyll theme configured
- **Build Process**: None (direct file serving)

## Development Workflows

### Working with This Repository

#### 1. Branch Strategy
- **Feature Branches**: All development work happens on feature branches
- **Branch Naming**: Use `claude/` prefix followed by descriptive name and session ID
  - Example: `claude/claude-md-mkpphx027qd8p4a3-MFIiz`
- **Main Branch**: Protected, requires pull requests for updates
- **No Direct Commits**: Never commit directly to main branch

#### 2. Development Cycle
```bash
# 1. Ensure you're on the correct feature branch
git branch --show-current

# 2. Make changes to files
# (Use appropriate tools: Write, Edit, etc.)

# 3. Stage and commit changes
git add <files>
git commit -m "Descriptive commit message"

# 4. Push to remote feature branch
git push -u origin <branch-name>

# 5. Create pull request when ready
gh pr create --title "Title" --body "Description"
```

#### 3. Commit Message Conventions
- **Format**: Use clear, imperative mood (e.g., "Add feature" not "Added feature")
- **Structure**:
  ```
  <type>: <short description>

  <optional detailed explanation>
  ```
- **Types**:
  - `feat:` - New feature
  - `fix:` - Bug fix
  - `docs:` - Documentation changes
  - `style:` - Formatting, styling changes
  - `refactor:` - Code restructuring
  - `content:` - Content additions/updates
  - `chore:` - Maintenance tasks

### Git Operations Best Practices

#### Push Operations
- Always use: `git push -u origin <branch-name>`
- Branch names MUST start with `claude/` and end with matching session ID
- Retry logic for network failures: up to 4 times with exponential backoff (2s, 4s, 8s, 16s)

#### Fetch/Pull Operations
- Prefer specific branches: `git fetch origin <branch-name>`
- Use: `git pull origin <branch-name>` for pulling
- Same retry logic as push operations

## Key Conventions for AI Assistants

### File Operations

#### Creating New Content
1. **Always Check First**: Use `Read` to check if file exists before creating
2. **Prefer Editing**: If a file exists, edit it rather than overwriting
3. **Use Appropriate Tools**:
   - `Read` - for reading files
   - `Edit` - for modifying existing files
   - `Write` - only for new files
   - `Glob` - for finding files by pattern
   - `Grep` - for searching content

#### Web Content Best Practices
When adding web content to this repository:

1. **HTML Files**:
   - Use semantic HTML5
   - Include proper DOCTYPE and meta tags
   - Ensure mobile responsiveness
   - Add `index.html` as the main landing page

2. **CSS Files**:
   - Use external stylesheets (prefer `styles/` or `css/` directory)
   - Follow mobile-first approach
   - Use CSS variables for theming

3. **JavaScript Files**:
   - Place in `js/` or `scripts/` directory
   - Use modern ES6+ syntax
   - Include comments for complex logic

4. **Assets**:
   - Images: `images/` or `assets/images/`
   - Documents: `docs/` or root directory
   - Fonts: `fonts/` or `assets/fonts/`

### GitHub Pages Specific Considerations

#### URL Structure
- Root: `https://arcidiaconom.github.io/`
- Files: `https://arcidiaconom.github.io/<filename>`
- Subdirectories: `https://arcidiaconom.github.io/<dir>/<file>`

#### Supported Features
- Static HTML, CSS, JavaScript
- Markdown files (automatically converted to HTML if Jekyll is enabled)
- PDF files (served directly)
- Images and media files
- Custom 404 pages (`404.html`)

#### Limitations
- No server-side processing (PHP, Node.js, etc.)
- No database support
- 1 GB repository size limit recommended
- 100 GB bandwidth limit per month
- 10 builds per hour if using Jekyll

### Code Quality Standards

#### When Adding Code
1. **Security First**: Never introduce vulnerabilities (XSS, injection, etc.)
2. **Accessibility**: Follow WCAG guidelines for web content
3. **Performance**: Optimize images, minify CSS/JS for production
4. **Compatibility**: Test across modern browsers
5. **Documentation**: Comment complex logic, maintain README

#### When Modifying Existing Code
1. **Read First**: Always read files before modifying
2. **Minimal Changes**: Only change what's necessary
3. **Preserve Style**: Match existing code style and formatting
4. **Test Impacts**: Consider downstream effects of changes
5. **No Over-engineering**: Avoid unnecessary abstractions

### Task Management

#### Using TodoWrite Tool
- Create todos for multi-step tasks (3+ steps)
- Update status in real-time:
  - `pending` - Not started
  - `in_progress` - Currently working (only ONE at a time)
  - `completed` - Finished
- Mark completed immediately after finishing
- Include both forms:
  - `content`: "Add homepage HTML"
  - `activeForm`: "Adding homepage HTML"

#### When to Skip TodoWrite
- Single, straightforward tasks
- Trivial operations (reading a file, simple edits)
- Purely informational requests

### Communication Standards

#### Output Format
- Use GitHub-flavored Markdown
- Be concise and direct
- No emojis unless requested
- Include file paths with line numbers: `file_path:line_number`

#### Response Style
- Technical accuracy over validation
- Objective, factual information
- No unnecessary superlatives
- Honest assessment of ideas
- Focus on facts and problem-solving

## Common Tasks

### Adding a Homepage
```bash
# 1. Create index.html
# 2. Add basic HTML structure
# 3. Test locally if possible
# 4. Commit and push
# 5. Verify on GitHub Pages
```

### Adding Styles
```bash
# 1. Create css/ or styles/ directory
# 2. Add stylesheet files
# 3. Link from HTML files
# 4. Commit and push
```

### Adding Documentation
```bash
# 1. Create docs/ directory or use root
# 2. Add markdown files
# 3. Link from main pages
# 4. Update README.md if needed
```

## Troubleshooting

### GitHub Pages Not Updating
- Check repository settings → Pages section
- Verify publishing source is correct
- Wait 5-10 minutes for propagation
- Clear browser cache
- Check for build errors in Actions tab (if Jekyll is enabled)

### Files Not Appearing
- Ensure files are committed and pushed
- Check file paths (case-sensitive)
- Verify files are in published branch
- Check file permissions

### Push Failures
- Verify branch name starts with `claude/`
- Check network connection
- Retry with exponential backoff
- Verify remote URL is accessible

## Future Expansion Possibilities

### Potential Additions
- **index.html**: Main landing page
- **about.html**: About page
- **contact.html**: Contact information
- **blog/**: Blog section with posts
- **projects/**: Portfolio/projects showcase
- **css/**: Stylesheet directory
- **js/**: JavaScript directory
- **images/**: Image assets
- **_config.yml**: Jekyll configuration (if needed)

### Framework Integration Options
- **Jekyll**: Built-in GitHub Pages support, blog-aware
- **Hugo**: Fast static site generator (requires Actions)
- **11ty**: Flexible, JavaScript-based (requires Actions)
- **Plain HTML/CSS/JS**: Maximum control, no build step

## Resources

### GitHub Pages Documentation
- [GitHub Pages Basics](https://docs.github.com/en/pages)
- [Jekyll on GitHub Pages](https://docs.github.com/en/pages/setting-up-a-github-pages-site-with-jekyll)
- [Custom Domains](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site)

### Web Development Best Practices
- [MDN Web Docs](https://developer.mozilla.org/)
- [Web.dev](https://web.dev/)
- [Can I Use](https://caniuse.com/) - Browser compatibility

### Accessibility
- [WCAG Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [A11y Project](https://www.a11yproject.com/)

## Version History

- **v1.0.0** (2026-01-22): Initial CLAUDE.md creation
  - Documented repository structure
  - Established development workflows
  - Defined conventions for AI assistants
  - Added GitHub Pages specific guidance

---

*This document should be updated whenever significant changes are made to the repository structure, workflow, or conventions.*
