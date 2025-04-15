/// <references types="houdini-svelte">

/** @type {import('houdini').ConfigFile} */
const config = {
    "schemaFile": "schema.graphql",
    "runtimeDir": ".houdini",
    "defaultCachePolicy": "CacheAndNetwork",
    "defaultFragmentMasking": "disable",
    "plugins": {
        "houdini-svelte": {
            "static": true,
            "forceRunesMode": true
        }
    },
    "exclude": ["src/lib/paraglide/**/*"],
    "scalars": {
        "JSON": {
            type: "unknown"
        }
    }
}

export default config