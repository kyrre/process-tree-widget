# Repository Guidelines

## Project Structure & Module Organization
This repository contains the following primary directories:

- `src/`: Source code
- `tests/`: Test suites and test cases
- `assets/`: Static resources (images, etc.)

## Build, Test, and Development Commands
To streamline development, use the following commands:

- `npm run build`: Compiles the source code.
- `npm test`: Runs the test suites.
- `npm start`: Starts the application locally.

## Coding Style & Naming Conventions
Adhere to the following style guidelines:

- **Indentation**: Use 4 spaces.
- **Naming**: Use camelCase for variables and functions, PascalCase for classes.
- **Linting**: Run `npm run lint` to ensure code quality.

## Testing Guidelines
Follow these testing conventions:

- **Framework**: Jest
- **Coverage**: Aim for 100% coverage, but minimum of 80%.
- **Naming**: Test files should mimic the naming of the source files followed by `.test.js`
- Run tests using `npm test`.

## Commit & Pull Request Guidelines
Ensure your commits and pull requests adhere to the following:

- **Commits**: Use descriptive messages. Start with a verb (e.g., Add, Fix), and be concise.
- **Pull Requests**: Include a clear description, link to relevant issues, and provide screenshots if applicable.

## Security & Configuration Tips
Keep these considerations in mind:

- **Environment Variables**: Store sensitive information in `.env` files and never commit them to the repository.
- **Dependencies**: Regularly check and update dependencies using `npm outdated` and `npm update`.

