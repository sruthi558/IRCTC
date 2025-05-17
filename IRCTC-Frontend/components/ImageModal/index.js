import styles from './ImageModal.module.scss'
import { useSelector, useDispatch } from 'react-redux'
import { disableImageModal, setImgUrl } from '../../store/slice/ModalPopup.js'
import { useState } from 'react'
import { faSpinner } from '@fortawesome/free-solid-svg-icons'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'

const ImageModal = ({ domain, setImageModalDomain }) => {
  const dispatch = useDispatch()
  const imageModal = useSelector((state) => state.modalPopup)
  const [imageLoaded, setImageLoaded] = useState(false)

  return (
    <div
      className={styles.ImageModalContainer}
      onClick={() => {
        dispatch(disableImageModal())
        dispatch(setImgUrl(''))
        setImageLoaded(false)
      }}
      style={{ display: imageModal.showImageModal ? 'flex' : 'none' }}
    >
      {imageLoaded ? null : (
        <div className={styles.loading}>
          <FontAwesomeIcon icon={faSpinner} spin size="5x" />
          <span className={styles.loadingText} size="5x">
            Loading...
          </span>
        </div>
      )}
      <img
        src={`${imageModal.imgUrl}`}
        onLoad={() => setImageLoaded(true)}
        style={{ display: imageLoaded ? 'block' : 'none' }}
      />
    </div>
  )
}

export default ImageModal