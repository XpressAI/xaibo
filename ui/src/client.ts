import { HoudiniClient } from '$houdini';
import { createClient } from 'graphql-ws'
import { subscription } from '$houdini/plugins'


export default new HoudiniClient({
    url: window.location.protocol+'//'+window.location.host+'/api/ui/graphql',
    plugins: [
        subscription(() => createClient({
            url: (window.location.protocol == 'http:' ? "ws:" : "wss:") + '//'+window.location.host+'/graphql'
        }))
    ],
})