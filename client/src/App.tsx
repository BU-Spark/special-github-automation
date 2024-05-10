import './App.css'
import { useDropzone } from 'react-dropzone';
import Box from '@mui/material/Box';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { useEffect, useState } from 'react';

function App() {

	const [infoloading, setInfoLoading] = useState(false);
	const [csvloading, setCsvLoading] = useState(false);
	const [inforows, setInfoRows] = useState<any[]>([]);
	const [csvrows, setCsvRows] = useState<any[]>([]);
	useEffect(() => {
		getinfo();
		getcsv();
	}, []);


	async function getinfo() {
		setInfoLoading(true);
		try {
			const response = await fetch('http://localhost:5000/getinfo');
			const data = await response.json();
			console.log(data);

			const info = data['info'];
			const rows = [];
			for (const i in info) {
				console.log(info[i]);
				const row = {
					id: i,
					buid: info[i]['buid'],
					name: info[i]['name'],
					email: info[i]['email'],
					github: info[i]['github'],
					semester: info[i]['semester'],
					project: info[i]['project_name'],
					repo: info[i]['repo'],
				};
				rows.push(row);
			}
			setInfoRows(rows);
		} catch (error) {
			console.error('Error fetching data:', error);
		} finally {
			setInfoLoading(false);
		}
	
	}

	async function getcsv() {
		setCsvLoading(true);
		try {
			const response = await fetch('http://localhost:5000/getcsv');
			const data = await response.json();
			console.log(data);

			const info = data['csv'];
			const rows = [];
			for (const i in info) {
				console.log(info[i]);
				const row = {
					id: i,
					semester: info[i]['semester'],
					course: info[i]['course'],
					project: info[i]['project'],
					organization: info[i]['organization'],
					team: info[i]['team'],
					role: info[i]['role'],
					fname: info[i]['fname'],
					lname: info[i]['lname'],
					name: info[i]['name'],
					email: info[i]['email'],
					buid: info[i]['buid'],
					github: info[i]['github'],
					process_status: info[i]['process_status'],
				};
				rows.push(row);
			}
			setCsvRows(rows);
		} catch (error) {
			console.error('Error fetching data:', error);
		} finally {
			setCsvLoading(false);
		}
	}

	async function onDrop(acceptedFiles: File[]) {
		setCsvLoading(true);
		const file = acceptedFiles[0];
		if (file) {
			/* uploadFile(file); */
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
					await getcsv();
					await getinfo();

					// call ingest api 

					const ingestreponse = await fetch('http://localhost:5000/ingest', {
						method: 'POST',
					});
					const ingestresult = await ingestreponse.json();
					if (ingestreponse.ok) {
						console.log('Ingested successfully:', ingestresult);
						await getcsv();
						await getinfo();
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
		setCsvLoading(false);
	};
	const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });

	const infocolumns: GridColDef[] = [
		{ field: 'id', headerName: 'ID', width: 90 },
		{
			field: 'buid',
			headerName: 'buid',
			editable: false,
		},
		{
			field: 'name',
			headerName: 'name',
			editable: false,
		},
		{
			field: 'email',
			headerName: 'email',
			editable: false,
		},
		{
			field: 'github',
			headerName: 'github',
			editable: false,
		},
		{
			field: 'semester',
			headerName: 'semester',
			editable: false,
		},
		{
			field: 'project',
			headerName: 'project',
			editable: false,
		},
		{
			field: 'repo',
			headerName: 'repo',
			editable: false,
		},

	];

	const csvcolumns: GridColDef[] = [
		{ field: 'id', headerName: 'ID', width: 90 },
		{
			field: 'semester',
			headerName: 'semester',
			editable: false,
		},
		{
			field: 'course',
			headerName: 'course',
			editable: false,
		},
		{
			field: 'project',
			headerName: 'project',
			editable: false,
		},
		{
			field: 'organization',
			headerName: 'organization',
			editable: false,
		},
		{
			field: 'team',
			headerName: 'team',
			editable: false,
		},
		{
			field: 'role',
			headerName: 'role',
			editable: false,
		},
		{
			field: 'fname',
			headerName: 'fname',
			editable: false,
		},
		{
			field: 'lname',
			headerName: 'lname',
			editable: false,
		},
		{
			field: 'name',
			headerName: 'name',
			editable: false,
		},
		{
			field: 'email',
			headerName: 'email',
			editable: false,
		},
		{
			field: 'buid',
			headerName: 'buid',
			editable: false,
		},
		{
			field: 'github',
			headerName: 'github',
			editable: false,
		},
		{
			field: 'process_status',
			headerName: 'process_status',
			editable: false,
		},

	];

	return (
		<>
			<h2>Current User Projects Repos Details</h2>
			<Box sx={{ height: 400, width: '100%', backgroundColor: "#242424"}}>
				<DataGrid
					rows={inforows}
					columns={infocolumns}
					initialState={{
						pagination: {
							paginationModel: {
								pageSize: 5,
							},
						},
					}}
					pageSizeOptions={[5]}
					checkboxSelection
					disableRowSelectionOnClick
					loading={infoloading}
					style={
						{
							backgroundColor: '#fff',
							color: 'black',
						}
					}
				/>
			</Box>
			<h2>Ingest User Project Repos Details</h2>
			<div {...getRootProps()} style={{ padding: 20, border: '2px dashed #007bff', borderRadius: 5, textAlign: 'center' }}>
				<input {...getInputProps()} />
				{
					isDragActive ?
						<p>Drop the file here ...</p> :
						<p>Drag and drop a CSV file here, or click to select a file</p>
				}
			</div>
			<Box sx={{ height: 400, width: '100%', backgroundColor: "#242424", marginTop: 2}}>
				<DataGrid
					rows={csvrows}
					columns={csvcolumns}
					initialState={{
						pagination: {
							paginationModel: {
								pageSize: 5,
							},
						},
					}}
					pageSizeOptions={[5]}
					checkboxSelection
					disableRowSelectionOnClick
					loading={csvloading}
					style={
						{
							backgroundColor: '#fff',
							color: 'black',
						}
					}
				/>
			</Box>
		</>
	)
}

export default App
