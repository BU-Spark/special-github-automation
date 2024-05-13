import './App.css'
import { useDropzone } from 'react-dropzone';
import Box from '@mui/material/Box';
import { DataGrid, GridColDef, GridRowSelectionModel } from '@mui/x-data-grid';
import { useEffect, useState } from 'react';
import { Button, Divider } from '@mui/material';
import { _csv, _git_repos, _info, _projects } from './fxns/fxns';
import General from './components/general/general';
import Csv from './components/csv/csv';
import Projects from './components/projects/projects';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Repos from './components/repos/repos';

interface TabPanelProps {
	children?: React.ReactNode;
	index: number;
	value: number;
}
function TabStyle(index: number) { return { id: `simple-tab-${index}`, 'aria-controls': `simple-tabpanel-${index}`, 'style': { color: '#fff' } }; }
function TabPanel(props: TabPanelProps) {
	const { children, value, index, ...other } = props;

	return (
		<div
			role="tabpanel"
			hidden={value !== index}
			id={`simple-tabpanel-${index}`}
			aria-labelledby={`simple-tab-${index}`}
			{...other}
		>
			{value === index && (<Box>{children}</Box>)}
		</div>
	);
}


function App() {

	const [value, setValue] = useState(0);
	const handleChange = (event: React.SyntheticEvent, newValue: number) => {
		setValue(newValue);
	};

	const [infoloading, setInfoLoading] = useState(false);
	const [csvloading, setCsvLoading] = useState(false);
	const [projectsloading, setProjectsLoading] = useState(false);
	const [reposloading, setReposLoading] = useState(false);
	const [inforows, setInfoRows] = useState<any[]>([]);
	const [csvrows, setCsvRows] = useState<any[]>([]);
	const [projectsrows, setProjectsRows] = useState<any[]>([]);
	const [reposrows, setReposRows] = useState<any[]>([]);
	useEffect(() => {
		getfxn(_info, setInfoLoading, setInfoRows);
		getfxn(_csv, setCsvLoading, setCsvRows);
		getfxn(_projects, setProjectsLoading, setProjectsRows);
		getfxn(_git_repos, setReposLoading, setReposRows);
	}, []);

	async function refresh() {
		await getfxn(_info, setInfoLoading, setInfoRows);
		await getfxn(_csv, setCsvLoading, setCsvRows);
		await getfxn(_projects, setProjectsLoading, setProjectsRows);
		await getfxn(_git_repos, setReposLoading, setReposRows);
	}


	async function getfxn(fxn: any, loadfxn: any, setfxn: any) {
		loadfxn(true);
		try {
			const rows = await fxn();
			setfxn(rows);
		}
		catch (error) { console.error('Error fetching data:', error); }
		finally { loadfxn(false); }
	}

	async function onDrop(acceptedFiles: File[]) {
		const file = acceptedFiles[0];
		if (file) {
			console.log(file);
			const formData = new FormData();
			formData.append("file", file);

			try {
				const response = await fetch('http://localhost:5000/upload', {
					method: 'POST',
					body: formData,
				});
				const result = await response.json();
				if (response.ok) {
					console.log('File uploaded successfully:', result);
					await getfxn(_csv, setCsvLoading, setCsvRows);

					const ingestreponse = await fetch('http://localhost:5000/ingest', {
						method: 'POST',
					});
					const ingestresult = await ingestreponse.json();
					if (ingestreponse.ok) {
						console.log('Ingested successfully:', ingestresult);
						await getfxn(_info, setInfoLoading, setInfoRows);
						await getfxn(_csv, setCsvLoading, setCsvRows);
						await getfxn(_projects, setProjectsLoading, setProjectsRows);
					} else {
						console.error('Failed to ingest:', ingestresult);
						throw new Error(ingestresult.message);
					}
				} else {
					console.error('Failed to upload file:', result);
					throw new Error(result.message);
				}
			} catch (error) {
				console.error('Error uploading file:', error);
			}
		}
	};

	const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });

	return (
		<>
			<h1>SPARK! AUTOMATIONS</h1>
			<Box sx={{ width: '100%' }}>
				<Tabs value={value} onChange={handleChange} aria-label="basic tabs example">
					<Tab label="Actions" 		{...TabStyle(0)} />
					<Tab label="Github CRUD" 	{...TabStyle(1)} />
					<Tab label="Retool" 		{...TabStyle(2)} />
				</Tabs>
			</Box>
			<Divider style={{ backgroundColor: '#fff', height: 3, marginTop: 20, marginBottom: 20 }} />

			<TabPanel value={value} index={0}>
				<h2>Current User Projects Repos Details</h2>
				<General infoloading={infoloading} inforows={inforows} />

				<Divider style={{ backgroundColor: '#fff', height: 1, marginTop: 20, marginBottom: 20 }} />

				<h2>Ingest User Project Repos Details</h2>
				<div {...getRootProps()} style={{ padding: 20, border: '2px dashed #007bff', borderRadius: 5, textAlign: 'center', cursor: 'pointer' }}>
					<input {...getInputProps()} />
					{
						isDragActive ?
							<p>Drop the file here ...</p> :
							<p>Drag and drop a CSV file here, or click to select a file</p>
					}
				</div>
				<Csv csvloading={csvloading} csvrows={csvrows} />

				<Divider style={{ backgroundColor: '#fff', height: 1, marginTop: 20, marginBottom: 20 }} />

				<h2>fxn: set selected projects to view only</h2>
				<Projects projectsloading={projectsloading} projectsrows={projectsrows} callback={refresh} />


			</TabPanel>
			<TabPanel value={value} index={1}>
				<>
				<h2>CRUD: ALL REPOS</h2>
				<Repos reposloading={reposloading} reposrows={reposrows} callback={refresh} />
				</>
			</TabPanel>
			<TabPanel value={value} index={2}>
				RETOOL
			</TabPanel>
		</>
	)
}

export default App
