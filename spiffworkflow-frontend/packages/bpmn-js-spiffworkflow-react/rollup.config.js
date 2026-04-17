import resolve from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import typescript from '@rollup/plugin-typescript';
import peerDepsExternal from 'rollup-plugin-peer-deps-external';
import postcss from 'rollup-plugin-postcss';

const createConfig = (input, outputName) => ({
  input,
  output: [
    {
      file: `dist/${outputName}.js`,
      format: 'cjs',
      sourcemap: true
    },
    {
      file: `dist/${outputName}.esm.js`,
      format: 'esm',
      sourcemap: true
    }
  ],
  plugins: [
    peerDepsExternal(),
    resolve({
      browser: true,
      preferBuiltins: false
    }),
    commonjs(),
    typescript({
      tsconfig: './tsconfig.json',
      declaration: true,
      declarationDir: 'dist',
      rootDir: 'src'
    }),
    postcss({
      extract: true,
      minimize: true
    })
  ],
  external: ['react', 'react-dom']
});

export default [
  createConfig('src/index.ts', 'index'),
  createConfig('src/modals.ts', 'modals')
];