import { getCookies } from "cookies-next"

const endPoint = process.env.API_ENDPOINT

export const validateUserCookiesFromSSR = async (req, res) => {
  let cookies = getCookies({ req, res })
  if (cookies.session) {
    let authenticateUser = await fetch(
      `${endPoint}/user`,
      {
        headers: {
          Accept: "application/json",
          Cookie: `session=${cookies.session}`,
       },
        method: "POST",
        credentials: "include",
      }
    )
    try {
      let jsonResponse = await authenticateUser.json();

    if (jsonResponse.email || jsonResponse.username || jsonResponse.id) {
      return {
          props: {},
      }
    }
    else {
      return {
        redirect: {
          destination: "/signin",
          permanent: false,
        },
        props: {},
      }
    }
  }
  catch(err) {
    return {
      redirect: {
        destination: "/signin",
        permanent: false,
      },
      props: {},
    }
  } 
  }

  else{
    return {
      redirect: {
        destination: "/signin",
        permanent: false,
      },
      props: {},
    }
  }
}
