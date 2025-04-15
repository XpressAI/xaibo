<script module>
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import MermaidDiagram from '$lib/components/custom/mermaid/MermaidDiagram.svelte';
	import { fn } from '@storybook/test';

	const flowchartDiagram = `
graph TD
    A[Start] --> B{Is it?}
    B -->|Yes| C[OK]
    C --> D[Rethink]
    D --> B
    B ---->|No| E[End]
`;

	const sequenceDiagram = `
sequenceDiagram
    participant Alice
    participant Bob
    Alice->>John: Hello John, how are you?
    loop Healthcheck
        John->>John: Fight against hypochondria
    end
    Note right of John: Rational thoughts <br/>prevail!
    John-->>Alice: Great!
    John->>Bob: How about you?
    Bob-->>John: Jolly good!
`;

	const classDiagram = `
classDiagram
    Animal <|-- Duck
    Animal <|-- Fish
    Animal <|-- Zebra
    Animal : +int age
    Animal : +String gender
    Animal: +isMammal()
    Animal: +mate()
    class Duck{
        +String beakColor
        +swim()
        +quack()
    }
    class Fish{
        -int sizeInFeet
        -canEat()
    }
    class Zebra{
        +bool is_wild
        +run()
    }
`;

	const ganttChart = `
gantt
    title A Gantt Diagram
    dateFormat  YYYY-MM-DD
    section Section
    A task           :a1, 2014-01-01, 30d
    Another task     :after a1  , 20d
    section Another
    Task in sec      :2014-01-12  , 12d
    another task      : 24d
`;

	const stateDiagram = `
stateDiagram-v2
    [*] --> Still
    Still --> [*]
    Still --> Moving
    Moving --> Still
    Moving --> Crash
    Crash --> [*]
`;

	const erDiagram = `
erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ LINE-ITEM : contains
    CUSTOMER }|..|{ DELIVERY-ADDRESS : uses
`;

	// More on how to set up stories at: https://storybook.js.org/docs/writing-stories
	const { Story } = defineMeta({
		title: 'Custom/MermaidDiagram',
		component: MermaidDiagram,
		tags: ['autodocs'],
		argTypes: {
			def: {
				control: 'text',
				description: 'Mermaid diagram definition'
			},
			config: {
				control: 'object',
				description: 'Mermaid configuration'
			}
		},
		args: {
			def: flowchartDiagram,
			config: {
				theme: 'default',
				securityLevel: 'loose'
			},
			onclick: fn()
		}
	});
</script>

<Story name="Flowchart" args={{ id: 'flowchart-diagram' }} />

<Story name="Sequence Diagram" args={{ id: 'sequence-diagram', def: sequenceDiagram }} />

<Story name="Class Diagram" args={{ id: 'class-diagram', def: classDiagram }} />

<Story name="Gantt Chart" args={{ id: 'gantt-chart', def: ganttChart }} />

<Story name="State Diagram" args={{ id: 'state-diagram', def: stateDiagram }} />

<Story name="ER Diagram" args={{ id: 'er-diagram', def: erDiagram }} />

<Story
	name="Dark Theme"
	args={{
		id: 'dark-theme-diagram',
		config: {
			theme: 'dark',
			securityLevel: 'loose'
		}
	}}
/>

<Story
	name="Forest Theme"
	args={{
		id: 'forest-theme-diagram',
		config: {
			theme: 'forest',
			securityLevel: 'loose'
		}
	}}
/>

<Story
	name="Neutral Theme"
	args={{
		id: 'neutral-theme-diagram',
		config: {
			theme: 'neutral',
			securityLevel: 'loose'
		}
	}}
/>
