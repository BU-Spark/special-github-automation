import { useDropzone } from 'react-dropzone';
import Box from '@mui/material/Box';
import { useEffect, useState } from 'react';
import { Divider } from '@mui/material';
import General from './components/general/general';
import Csv from './components/csv/csv';
import Projects from './components/projects/projects';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Repos from './components/repos/repos';
import { API_URL } from './utils/uri';
import { useAuth } from './context/auth';
import { useFxns } from './context/fxns';

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

	const { _fetch, credentials } = useAuth();
	const { _csv, _git_repos, _info, _projects } = useFxns();

	const [value, setValue] = useState(0);
	const handleChange = (event: React.SyntheticEvent, newValue: number) => {
		console.log(event);
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
				const response = await fetch(`${API_URL}/upload`, {
					headers: {
						'Authorization': 'Basic ' + btoa(credentials.username + ":" + credentials.password),
					},
					method: 'POST',
					body: formData,
				});
				const result = await response.json();
				if (response.ok) {
					console.log('File uploaded successfully:', result);
					await getfxn(_csv, setCsvLoading, setCsvRows);

					const ingestreponse = await _fetch(`${API_URL}/ingest`, {
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
	}

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
				<h4>General information about students & projects</h4>
				<General infoloading={infoloading} inforows={inforows} />

				<Divider style={{ backgroundColor: '#fff', height: 1, marginTop: 20, marginBottom: 20 }} />

				<h2>Ingest User Project Repos Details</h2>
				<h4>Upload CSV file. (this will automatically make any projects or users as needed)</h4>
				<div {...getRootProps()} style={{ padding: 20, border: '2px dashed #007bff', borderRadius: 5, textAlign: 'center', cursor: 'pointer' }}>
					<input {...getInputProps()} />
					{
						isDragActive ?
							<p>Drop the file here ...</p> :
							<p>Drag and drop a CSV file here, or click to select a file</p>
					}
				</div>
				<Csv csvloading={csvloading} csvrows={csvrows} callback={refresh} />

				<Divider style={{ backgroundColor: '#fff', height: 1, marginTop: 20, marginBottom: 20 }} />

				<h2>Set selected projects to Push/Pull</h2>
				<h4>Select the projects you want to change to view / write</h4>
				<Projects projectsloading={projectsloading} projectsrows={projectsrows} callback={refresh} />


			</TabPanel>
			<TabPanel value={value} index={1}>
				<>
				<h2>CRUD: ALL REPOS</h2>
				<Repos reposloading={reposloading} reposrows={reposrows} />
				</>
			</TabPanel>
			<TabPanel value={value} index={2}>
				<iframe src="https://testgithub.retool.com/apps/automation%20dashboard" width="100%" height="800px"></iframe>
			</TabPanel>
		</>
	)
}

export default App
