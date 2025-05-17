import '../styles/globals.scss'
import Head from 'next/head'
import 'react-toastify/dist/ReactToastify.css'
import 'bootstrap/dist/css/bootstrap.min.css'
import '../styles/globals.css'

import { PersistGate } from 'redux-persist/integration/react'

import { useEffect } from 'react'

// Redux
import { Provider } from 'react-redux'
import { store, persistor } from '../store'

import ImageModal from '../components/ImageModal'

import { ToastContainer } from 'react-toastify'

export default function App({ Component, pageProps }) {
  useEffect(() => {
    require('bootstrap/dist/js/bootstrap.bundle.min.js')
  }, [])

  return (
    <>
      <Head>
        <title>IRCTC | Dashboard</title>
      </Head>
      <ToastContainer
        position="top-center"
        autoClose={2000}
        closeOnClick
        hideProgressBar={false}
        theme="light"
      />
      <Provider theme="dark" loading={null} store={store}>
        <PersistGate loading={null} persistor={persistor}>
          <ImageModal />
          <Component {...pageProps} />
        </PersistGate>
      </Provider>
    </>
  )
}
