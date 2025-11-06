# Branching Model

This document describes the branching model for ZeroUI 2.0 development.

## Model: Trunk-Based Development with Small PRs

We use **trunk-based development** with small, frequent pull requests to the main branch.

## Branch Types

### Main Branch (`main`)

- **Purpose**: Production-ready code
- **Protection**: Protected branch, requires PR approval
- **Deployment**: Automatically deployed to production after merge
- **Status**: Always stable and deployable

### Feature Branches (`feature/<name>`)

- **Purpose**: Development of new features
- **Naming**: `feature/<descriptive-name>`
- **Lifetime**: Short-lived (hours to days)
- **Merge**: Merged to `main` via PR when complete

### Hotfix Branches (`hotfix/<name>`)

- **Purpose**: Critical production fixes
- **Naming**: `hotfix/<issue-number>`
- **Lifetime**: Very short (hours)
- **Merge**: Merged to `main` and `release/*` branches

### Release Branches (`release/<version>`)

- **Purpose**: Release preparation and stabilization
- **Naming**: `release/v<major>.<minor>.<patch>`
- **Lifetime**: Days to weeks
- **Merge**: Merged to `main` when release is complete

## Workflow

### Feature Development

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/add-gate-table-loader
   ```

2. **Develop and Commit**
   ```bash
   # Make small, atomic commits
   git add .
   git commit -m "feat: add gate table CSV loader"
   ```

3. **Push and Create PR**
   ```bash
   git push origin feature/add-gate-table-loader
   # Create PR via GitHub/GitLab UI
   ```

4. **Review and Merge**
   - PR reviewed by at least one team member
   - CI/CD checks pass
   - Merge to `main`

5. **Delete Branch**
   - Branch automatically deleted after merge

### Hotfix Workflow

1. **Create Hotfix Branch from main**
   ```bash
   git checkout main
   git pull
   git checkout -b hotfix/fix-receipt-write
   ```

2. **Fix and Test**
   ```bash
   # Make fix
   git commit -m "fix: receipt write failure"
   ```

3. **Merge to main and release branches**
   ```bash
   git checkout main
   git merge hotfix/fix-receipt-write
   git checkout release/v1.0.0
   git merge hotfix/fix-receipt-write
   ```

## PR Guidelines

### PR Size

- **Small PRs**: < 200 lines changed (preferred)
- **Medium PRs**: 200-500 lines changed (acceptable)
- **Large PRs**: > 500 lines changed (requires justification)

### PR Description

Every PR must include:
- **What**: What changes are made
- **Why**: Why these changes are needed
- **How**: How the changes work
- **Testing**: How changes were tested

### PR Checklist

- [ ] Code follows coding standards
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] CI/CD checks pass
- [ ] Reviewed by at least one team member

## Commit Messages

### Format

```
<type>: <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

### Examples

```
feat: add gate table CSV loader

Implements CSV parsing for gate decision tables.
Supports condition, threshold, decision, reason_code, priority columns.

Closes #123
```

```
fix: receipt write failure on Windows

Fixes path resolution issue on Windows by using path.join().

Fixes #456
```

## Branch Protection

### Main Branch Protection

- **Required Reviews**: At least 1 approval
- **Required Status Checks**: All CI/CD checks must pass
- **No Force Push**: Force push disabled
- **No Direct Push**: All changes via PR

### Release Branch Protection

- **Required Reviews**: At least 2 approvals
- **Required Status Checks**: All CI/CD checks must pass
- **No Force Push**: Force push disabled

## CI/CD Integration

### PR Checks

Every PR triggers:
- **Linting**: Code style checks
- **Tests**: Unit and integration tests
- **Build**: Verify code compiles
- **Security Scan**: Dependency and code scanning

### Merge Checks

Before merge:
- **All Checks Pass**: All CI/CD checks must pass
- **No Conflicts**: Branch must be up to date with main
- **Approval**: Required number of approvals

## Best Practices

1. **Keep Branches Short-Lived**: Merge within days, not weeks
2. **Small PRs**: Prefer multiple small PRs over one large PR
3. **Frequent Sync**: Regularly sync with main branch
4. **Clear Commits**: Write clear, descriptive commit messages
5. **Test Before PR**: Ensure tests pass before creating PR

## Conflict Resolution

### When Conflicts Occur

1. **Sync with main**
   ```bash
   git checkout main
   git pull
   git checkout feature/my-feature
   git merge main
   ```

2. **Resolve conflicts**
   ```bash
   # Edit conflicted files
   # Resolve conflicts
   git add .
   git commit -m "merge: resolve conflicts with main"
   ```

3. **Push updated branch**
   ```bash
   git push origin feature/my-feature
   ```

## Release Process

1. **Create Release Branch**
   ```bash
   git checkout -b release/v1.0.0
   ```

2. **Stabilize and Test**
   - Fix bugs
   - Update documentation
   - Run full test suite

3. **Tag Release**
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```

4. **Merge to main**
   ```bash
   git checkout main
   git merge release/v1.0.0
   git push origin main
   ```

## Emergency Procedures

### Critical Hotfix

1. Create hotfix branch from main
2. Make minimal fix
3. Test thoroughly
4. Get emergency approval
5. Merge to main immediately
6. Deploy to production
7. Create follow-up PR for documentation

