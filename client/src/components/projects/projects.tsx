import { Box, Button, CircularProgress } from "@mui/material";
import { DataGrid, GridColDef, GridRowSelectionModel } from "@mui/x-data-grid";
import React, { useState } from "react";
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';

export default function Projects({ projectsloading, projectsrows, callback }: any) {

    const projectcolumns: GridColDef[] = [
        { field: 'id', headerName: 'ID', flex: .25 },
        {
            field: 'name',
            headerName: 'name',
            editable: false,
            flex: 1,
        },
        {
            field: 'github_url',
            headerName: 'github url',
            editable: false,
            flex: 1,
        },
        {
            field: 'semester',
            headerName: 'semester',
            editable: false,
            flex: 1,
        },
    ];

    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState<any[]>([]);
    const [selectedProjectsUrls, setSelectedProjectsUrls] = useState<string[][]>([]);
    async function selectionchange(selection: GridRowSelectionModel) {
        const selectedprojects = selection.map((selected) => [projectsrows[selected as number].name, projectsrows[selected as number].github_url]);
        console.log('Selected projects:', selectedprojects);
        setSelectedProjectsUrls(selectedprojects);
    }
    async function setProjectsTo(action: "push" | "pull") {

        if (selectedProjectsUrls.length === 0) {
            setResults(['No projects selected']);
            return;
        }

        setLoading(true);
        console.log('Setting projects to', action);
        console.log('Selected projects:', selectedProjectsUrls);

        try {
            const response = await fetch('http://localhost:5000/set_projects', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    action: action,
                    projects: selectedProjectsUrls
                })
            });
            const result = await response.json();
            console.log('Result:', result);
            if (response.ok) {
                console.log('Projects set successfully:', result);
                setResults(result['results']);
            } else throw new Error('Error setting projects');
        } catch (error : any) {
            console.error('Error setting projects:', error);
            setResults([
                'Error setting projects ' + error.toString()
            ]);
        } finally {
            setLoading(false);
            callback();
        }
    }

    return (
        <>
            <Box sx={{ height: 400, width: '100%', backgroundColor: "#242424", marginBottom: 2 }}>
                <DataGrid
                    rows={projectsrows}
                    columns={projectcolumns}
                    initialState={{
                        pagination: {
                            paginationModel: {
                                pageSize: 5,
                            },
                        },
                    }}
                    pageSizeOptions={[5]}
                    disableRowSelectionOnClick
                    checkboxSelection
                    onRowSelectionModelChange={selectionchange}
                    loading={projectsloading}
                    style={
                        {
                            backgroundColor: '#fff',
                            color: 'black',
                        }
                    }
                />
            </Box>
            {
                loading ?
                <Box sx={{ display: 'flex', marginTop: 2 }}>
                    <CircularProgress />
                </Box>
                :
                <Box sx={{ display: 'flex', gap: 2 }}>
                    <Button variant='contained' color='primary' onClick={() => setProjectsTo('pull')}>
                        Set selected projects to (pull)
                    </Button>
                    <Button variant='contained' color='primary' onClick={() => setProjectsTo('push')}>
                        Set selected projects to (push)
                    </Button>
                </Box>
            }

            <TableContainer component={Paper} sx={{ marginTop: 2 }}>
                <Table sx={{ minWidth: 650 }} size="small" aria-label="a dense table">
                    <TableHead>
                        <TableRow>
                            <TableCell size="small" sx={{ width: '40px' }}>idx</TableCell>
                            <TableCell>results</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {results.map((row, idx) => (
                            <TableRow
                                key={idx}
                                sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                            >
                                <TableCell size="small">{idx}</TableCell>
                                <TableCell size="small">{row}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
            
        </>
    );
}