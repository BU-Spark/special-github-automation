import { Box } from "@mui/material";
import { DataGrid, GridColDef } from "@mui/x-data-grid";
import React, { useState } from "react";

export default function General({ infoloading, inforows }: any) {

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
    return (
        <>
            <Box sx={{ height: 400, width: '100%', backgroundColor: "#242424" }}>
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
        </>
    )
}