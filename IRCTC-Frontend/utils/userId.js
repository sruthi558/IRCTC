export const getMoreUserID = async (currentPage, dispatch) => {
	const raw = await fetch('/api/userid_list',{
		method: "POST",
		headers: {
			Accept: 'application/json',
			"Content-Type": 'application/json'
		},
		credentials: 'include',
		body: JSON.stringify({
			page_id: currentPage + 1
		})
	})
	const data = await raw.json()
	const parsedData = data.map((item) => JSON.parse(item))

	return parsedData
}