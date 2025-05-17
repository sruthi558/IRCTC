import { Table, Pagination } from 'rsuite'
import { useState } from 'react'




function NotificationComp(prop) {
    
    const [loading, setLoading] = useState(true)
    return (
        <div className="col mx-auto" style={{
            display: 'block', paddingLeft: 30, marginTop: 20
        }}>
      <Table loading={loading} bordered cellBordered autoHeight data={useridData}>
        <Column width={150} >
          <HeaderCell>User ID</HeaderCell>
          <CompactCell >{rowData => {
          return rowData.USER_ID;
        }}
          </CompactCell>
        </Column>
        <Column width={150}>
          <HeaderCell>First Name</HeaderCell>
          <CompactCell dataKey="USER_NAME" />
        </Column>
        <Column width={170} fullText>
          <HeaderCell>Created on</HeaderCell>
          <CompactCell dataKey="TXN_DT_TIME.$date" />
        </Column>
        <Column width={150}> 
          <HeaderCell>IP Address</HeaderCell>
          <CompactCell dataKey="FMT_CLIENT_IP_ADDRESS" />
        </Column>
        <Column width={150} fullText>
          <HeaderCell>ISP</HeaderCell>
          <CompactCell dataKey="ISP" />
        </Column>
        <Column width={150}>
          <HeaderCell>ASN</HeaderCell>
          <CompactCell dataKey="ASN" />
        </Column>
        <Column width={150}>
          <HeaderCell>Country</HeaderCell>
          <CompactCell dataKey="COUNTRY" />
        </Column>
        <Column width={150}>
          <HeaderCell>VPS</HeaderCell>
          <CompactCell >
          {rowData => { return (rowData.VPS) ? 'True' : 'False'}}
            </CompactCell>
        </Column>
        <Column width={150}>
          <HeaderCell>Vendor</HeaderCell>
          <CompactCell >
            {rowData => { return (rowData.VENDOR_NAME) ? rowData.VENDOR_NAME : 'None'}}
            </CompactCell>
        </Column>
        <Column width={100}>
          <HeaderCell>Status</HeaderCell>
          <CompactCell >
          {rowData => { return (rowData.VPS) ? 'True' : 'Pending'}}
            </CompactCell>
        </Column>
        <Column width={50}>
                <HeaderCell>
                  <MoreIcon />
                </HeaderCell>
                <ActionCell />
              </Column>
      </Table>
      <div style={{ padding: 20 }}>
        <Pagination
          prev
          next
          first
          last
          ellipsis
          boundaryLinks
          maxButtons={5}
          size="xs"
          layout={['total', '-', 'limit', '|', 'pager', 'skip']}
          total={useridPageCount}
          limit={limit}
          activePage={page}
          onChangePage={handlePageChange}
          onChangeLimit={handleChangeLimit}
        />
      </div>
     </div>
    )
}

export default NotificationComp;