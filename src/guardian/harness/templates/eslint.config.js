import tseslint from '@typescript-eslint/eslint-plugin';
import tsparser from '@typescript-eslint/parser';
import eslintComments from '@eslint-community/eslint-plugin-eslint-comments';

export default [
  {
    files: ['**/*.ts', '**/*.tsx', '**/*.js', '**/*.jsx'],
    languageOptions: {
      parser: tsparser,
    },
    plugins: {
      '@typescript-eslint': tseslint,
      'eslint-comments': eslintComments,
    },
    rules: {
      // Ban all TypeScript suppress comments
      '@typescript-eslint/ban-ts-comment': ['error', {
        'ts-expect-error': true,
        'ts-ignore': true,
        'ts-nocheck': true,
        'ts-check': false,
        minimumDescriptionLength: 0,
      }],

      // Ban explicit 'any' type
      '@typescript-eslint/no-explicit-any': 'error',

      // Require specific rules in eslint-disable comments
      'eslint-comments/no-unlimited-disable': 'error',
      'eslint-comments/require-description': ['error', {
        ignore: [],
      }],

      // Detect .skip() and .only() in tests
      'no-restricted-syntax': ['error', {
        selector: 'CallExpression[callee.property.name=/^(skip|only)$/]',
        message: 'Skipped or focused tests are not allowed',
      }],
    },
  },
];
