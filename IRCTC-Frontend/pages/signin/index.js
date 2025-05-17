// Import Libraries
import { toast } from 'react-toastify'
import { getCookies } from 'cookies-next'
import { useRouter } from 'next/router'
import { useDispatch } from 'react-redux'
import { useState, useEffect } from 'react'

// Import Styles
import styles from './signin.module.scss'

// Import Store
import { setRole, setDept, addUserPages, addUserActions } from '../../store/slice/user'
import { TRUE } from 'sass'

const endPoint = process.env.API_ENDPOINT

// SignIn Page
const SignIn = () => {
  // Initialise React router for routing after a successful signin.
  const router = useRouter()

  // Initialise states to collect user inputs for username and password.
  const [email, setEmail] = useState('')
  
  const [password, setPassword] = useState('')

  // Enable/disable form submit button to ensure user provides all fields, & does not send multiple requests.
  const [submitDisabled, setSubmitDisabled] = useState(true)

  // Handling Captcha Verification!!
  const [captcha, setCaptcha] = useState('')
  const [captchaAnswer, setCaptchaAnswer] = useState('')
  const [isVerified, setIsVerified] = useState(false)

  useEffect(() => {
    generateCaptch();
  }, [])

  const generateCaptch = () => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789#@$'
    let captchaStr = '';
    for (let i=0; i<6; i++) {
      captchaStr += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    setCaptcha(captchaStr); 
  }

  const handleVerification = () => {
    if (captchaAnswer === captcha) {
      // toast.info('Verification Successfull!')
      setIsVerified(true); 
    } else {
      toast.error('Verification Failed!')
      setIsVerified(false); 
      generateCaptch(); 
      setCaptchaAnswer(''); 
    }
  }

  // Initialise state dispatcher.
  const dispatch = useDispatch()

  // Requests backend to authenticate the user with credentials in payload.
  const getSignInCredentials = async (email, password, dispatch) => {
    // Disable the submit button till the server returns a response to prevent multiple requests.
    setSubmitDisabled(true)

    const authenticatedFlag = await fetch('/api/signin', {
      headers: {
        'content-type': 'application/json',
        accept: '*/*',
      },
      credentials: 'same-origin',
      method: 'POST',
      mode: 'cors',
      body: JSON.stringify({
        email: email,
        password: password,
      }),
    }).then((response) => response.json())

    if ('user_pages' in authenticatedFlag && 'user_actions' in authenticatedFlag && 'role' in authenticatedFlag && 'dept' in authenticatedFlag) {
      console.log(authenticatedFlag, `type: ${typeof(authenticatedFlag)}`);
      // set user_pages data 
      dispatch(addUserPages(authenticatedFlag['user_pages']))
      // set user role 
      dispatch(setRole(authenticatedFlag['role']))
      // set user dept. 
      dispatch(setDept(authenticatedFlag['dept']))
      // set allowed user actions 
      dispatch(addUserActions(authenticatedFlag['user_actions']))

      console.log(`User value datta set!!`);
      return true; 
    } else {
      toast.error(`Please enter correct password/email.`)
      return false; 
    }

    // --------------------------------------------------

    // // condition for display user_pages on siebar after loggin with that perticular mailId.
    // // do uncomment code and check it out.

    // // Check if the 'user_pages' key exists in the authenticatedFlag object.    
    // if ('user_pages' in authenticatedFlag) {
    //   dispatch(addUserPages(authenticatedFlag?.user_pages))
    // }

    // // If 'role' key exists in the authenticatedFlag object & dispatch action to set the user's department 
    // if ('role' in authenticatedFlag) {
    //   dispatch(setRole(authenticatedFlag['role']))
    //   dispatch(setDept(authenticatedFlag['dept']))
    //   // Return true to indicate successful authentication.
    //   return true
    // }

    // // If the 'user_pages' or 'role' key does not exist in the authenticatedFlag object,
    // // display an error message using the 'toast' library and return false to indicate
    // // unsuccessful authentication.
    // toast.error('Please enter the correct password/username!')
    // return false
  }

  // Define authentication functionality to verify user provided credentials.
  const handleAuthenticationSubmit = async (event) => {
    // Prevent page autoreload.
    event.preventDefault()

    // Perform network requests to verify user provided credentials from the backend.
    let authenticatedFlag = await getSignInCredentials(
      email,
      password,
      dispatch,
    )

    // Reset user input fields.
    setEmail('')
    setPassword('')

    // Take the action as per the authentication status.
    if (authenticatedFlag) {
      router.push('/overview')
    } else {
      // Enable the submit button as the server has returned a response.
      setSubmitDisabled(false)
    }
  }

  // Set the state of the fields as per user input.
  const handleInput = (event) => {
    switch (event.target.name) {
      // Set email state from user input.
      case 'email':
        setEmail(event.target.value)
        break

      // Set password state from user input.
      case 'password':
        setPassword(event.target.value)
        break
    }
  }

  // Change state of submit button as per change in user input.
  useEffect(() => {
    if (email === '' || password === '') {
      // Disable submit button if any of the user input fields are empty.
      setSubmitDisabled(true)
    } else {
      // Enable submit button if both user input fields are filled.
      setSubmitDisabled(false)
    }
  }, [email, password])

  // Render
  return (
    <div className={styles.container}>
      <div className={styles.signInBox}>
        <div className={styles.signInForm}>
          <div className={styles.logo}>
            <img src={'./static/images/logo.png'} />
          </div>
          <form className={styles.form}>
            <input
              type="text"
              id="email"
              name="email"
              placeholder="Email"
              value={email}
              onChange={handleInput}
              className={styles.placeholderColor}
            />

            <input
              type="password"
              id="password"
              name="password"
              placeholder="Password"
              value={password}
              onChange={handleInput}
              className={styles.placeholderColor}
            />

            {isVerified && (
              <button type="submit" onClick={handleAuthenticationSubmit}>
                <h5>SIGN IN</h5>
              </button>
            )}

            {/* {isVerified ? (
              <button type="submit" onClick={handleAuthenticationSubmit}>
                <h5>SIGN IN</h5>
              </button>
            ) : (
              <div className={styles.captcha_container}>
                <div className={styles.captcha_text}>{captcha}</div>
                <input
                  type='text'
                  value={captchaAnswer}
                  className={styles.captcha_input}
                  // className={styles.placeholderColor}
                  placeholder='Enter the above Characters'
                  onChange={(e) => setCaptchaAnswer(e.target.value)}
                />
                <button className={styles.captcha_btn} onClick={handleVerification}>verify</button>
              </div>
            )} */}
          </form>
          
          {/* Verification Captcha */}
          {
            isVerified === false ? (
              <div className={styles.captcha_container}>
                <div className={styles.captcha_text}>{captcha}</div>
                <input
                  type='text'
                  value={captchaAnswer}
                  className={styles.captcha_input}
                  // className={styles.placeholderColor}
                  placeholder='Enter Captcha'
                  onChange={(e) => setCaptchaAnswer(e.target.value)}
                />
                <span className={styles.captcha_btn} onClick={handleVerification}>verify</span>
              </div>
            ) : ""
          }
          
        </div>
      </div>
      {/* <div className={styles.Footer}>
        <h4>
          Powered by <img src={'./static/images/pinaca.png'} />
        </h4>
      </div> */}
    </div>
  )
}

// Server Side Rendering
export async function getServerSideProps({ req, res }) {
  // Fetch cookies from the request.
  const cookies = getCookies({ req, res })

  // Check if a valid session exists.
  if (cookies.session) {
    // Validate the user with the cookie.Overview
    let authenticateUser = await fetch(`${endPoint}/user`, {
      headers: {
        Accept: 'application/json',
        Cookie: `session=${cookies.session}`,
      },
      method: 'POST',
      credentials: 'same-origin',
    })

    try {
      // Parse JSON response from server for authenticated user.
      let jsonResponse = await authenticateUser.json()

      // If either of the parameters exist, redirect the user to the overview page.
      if (jsonResponse.email || jsonResponse.username || jsonResponse.id) {
        return {
          redirect: {
            permanent: false,
            destination: '/overview',
          },
        }
      }
    } catch (err) {
      return {
        props: {},
      }
    }
  }
  return {
    props: {},
  }
}

// Export SignIn Page
export default SignIn
