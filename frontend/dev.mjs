import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';
const root=dirname(fileURLToPath(import.meta.url));
const backend=spawn(process.env.PYTHON||'python',['-m','uvicorn','main:app','--host','127.0.0.1','--port','8000'],{cwd:resolve(root,'../backend'),stdio:'inherit'});
const worker=spawn(process.env.PYTHON||'python',['worker.py'],{cwd:resolve(root,'../backend'),stdio:'inherit'});
const frontend=spawn(process.execPath,[resolve(root,'node_modules/vite/bin/vite.js'),'--host','0.0.0.0',...process.argv.slice(2)],{cwd:root,stdio:'inherit'});
let stopping=false;function stop(){if(stopping)return;stopping=true;backend.kill();worker.kill();frontend.kill()}
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,stop);
for(const [name,child] of [['API',backend],['Reminder worker',worker],['Frontend',frontend]]){
 child.on('error',error=>{console.error(`${name} failed to start: ${error.message}`);process.exitCode=1;stop()});
 child.on('exit',(code,signal)=>{if(stopping)return;console.error(`${name} stopped (${signal||code}). Stopping the development stack.`);process.exitCode=code||1;stop()});
}
