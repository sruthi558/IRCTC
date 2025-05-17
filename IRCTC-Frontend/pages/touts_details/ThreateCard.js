// ThreatCard.js
import React, { useState } from "react";
import { Panel, Modal, Pagination } from "rsuite";
import styles from "./touts-details.module.scss";

import CloseIcon from "@rsuite/icons/Close";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faMobileAlt,
  faAddressCard,
  faEnvelope,
  faGlobe,
  faUser,
  faStar,
} from "@fortawesome/free-solid-svg-icons";
import {
  faYoutube,
  faTelegram,
  faWhatsapp,
} from "@fortawesome/free-brands-svg-icons";

const ThreatCard = ({ data }) => {
  const [modalOpen, setModalOpen] = useState(false);

  const handleReadMore = () => {
    setModalOpen(true);
    document.body.classList.add(styles.blurred);
  };

  const handleCloseModal = () => {
    setModalOpen(false);
    document.body.classList.remove(styles.blurred);
  };

  const renderContactInfo = (Contact) => {
    if (!Array.isArray(Contact) || Contact?.every((contact) => !contact)) {
      return null;
    }
  
    return Contact.map((contact, index) => {
      // Convert the string to a number and then back to a string to remove the trailing .0
      const cleanedContact = Number(contact)?.toString();
  
      // Remove trailing zeros after the decimal point or dot. 
      const formattedContact = cleanedContact?.includes('.')
        ? cleanedContact?.replace(/\.?0*$/, '')
        : cleanedContact;
  
      return (
        <div key={index} className={styles.contactInfo}>
          <FontAwesomeIcon
            icon={faAddressCard}
            className={styles.fontIconStyling}
          />
          <span className={styles.contactdotStyling}>:</span>
          <span>{formattedContact}</span>
        </div>
      );
    });
  };
  

  const renderEmails = (emails) => {
    if (!Array.isArray(emails) || emails?.every((email) => !email)) {
      return null;
    }

    return emails.map((email, index) => (
      <div key={index} className={styles.email}>
        <FontAwesomeIcon icon={faEnvelope} className={styles.fontIconStyling} />
        <span className={styles.dotStyling}>:</span>
        <span>{email}</span>
      </div>
    ));
  };

  const renderSocialLinks = (socialLinks, type) => {
    if (!Array.isArray(socialLinks) || socialLinks?.every((link) => !link)) {
      return null;
    }

    const iconMapping = {
      YouTube: faYoutube,
      telegram: faTelegram,
      WhatsApp: faWhatsapp,
      whatsapp: faWhatsapp,
      website: faGlobe,
      others: faStar,
    };

    return (
      <>
        <div className={styles.socialLink}>
          {socialLinks.map(
            (link, index) =>
              link && (
                <span key={index} className={styles.socialLinkItem}>
                  <a href={link} target="_blank" rel="noopener noreferrer">
                    {iconMapping[type] && (
                      <FontAwesomeIcon
                        icon={iconMapping[type]}
                        className={styles.fontIconStyling}
                      />
                    )}
                  </a>
                  <span className={styles.dotStyling}>:</span>
                  <a
                    href={link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={styles.linkText}
                  >
                    {link?.length > 35 ? `${link?.slice(0, 35)} ...` : link}
                  </a>
                </span>
              )
          )}
        </div>
      </>
    );
  };

  const shouldDisplayReadMore =
    data?.Contact?.length > 1 ||
    data?.Email?.length > 1 ||
    data?.Youtube?.length > 1 ||
    data?.Telegram?.length > 1 ||
    data?.Website?.length > 1 ||
    data?.Whatsapp?.length > 1 ||
    data?.Others?.length > 1;

  // const shouldDisplayReadMore = Object.keys(data).length > 8;
  // const shouldDisplayReadMore = Object.keys(data).filter(key => data[key] && data[key].length > 0).length > 6;

  // const displayKeysInCard = 6;
  const displayKeysInModal = Object.keys(data)?.length;

  const keyIconMapping = {
    contact: faAddressCard,
    email: faEnvelope,
    youtube: faYoutube,
    telegram: faTelegram,
    whatsapp: faWhatsapp,
    website: faGlobe,
    name: faUser,
    others: faStar,
  };

  const hasImage =
    data?.Image && data?.Image?.$binary && data?.Image?.$binary?.base64;

  const renderImage = () => {
    if (hasImage) {
      return (
        <img
          src={`data:image/jpeg;base64,${data?.Image?.$binary?.base64}`}
          alt="Profile"
          width="100%"
          height="150"
          className={styles.card_Image}
        />
      );
    }

    return (
      <img
        src="/static/images/User-Profile.png"
        alt="Profile"
        width="100%"
        height="150"
        className={styles.bg_default_card_Image}
      />
    );
  };

  const isValidUrl = (url) => {
    const pattern =
      /^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9]+([-.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$/;
    return pattern?.test(url);
  };

  return (
    <>
      <Panel bordered className={styles.threatCard}>
        <div className={styles.header}>
          <div className={styles.ImageDiv}>
            <img
              src="/static/images/IJhNWg.jpg"
              alt="Profile"
              width="100%"
              height="150"
              className={styles.bg_card_Image}
            />
          </div>
          <div className={styles.parrentProfileImage}>
            <div className={styles.mainProfileImage}>
              {/* {data?.Image && data?.Image?.$binary && (
                <img
                  src={`data:image/jpeg;base64,${data?.Image?.$binary?.base64}`}
                  alt="Profile"
                  width="100%"
                  height="150"
                  className={styles.card_Image}
                />
              )} */}
              {renderImage()}
            </div>
          </div>
          <div className={styles.userName}>{data?.Name[0]}</div>
        </div>
        <div className={styles.backgroundWrapper}>
          {/* <div className={styles.profileName}>{data.name[0]}</div> */}
          <div className={styles.contactDetails}>
            {renderContactInfo(data?.Contact?.slice(0, 2))}
            {renderEmails(data?.Email?.slice(0, 2))}
            {renderSocialLinks(data?.Youtube?.slice(0, 2), "YouTube")}
            {renderSocialLinks(data?.Telegram?.slice(0, 2), "telegram")}
            {renderSocialLinks(data?.Website?.slice(0, 2), "website")}
            {renderSocialLinks(data?.Whatsapp?.slice(0, 2), "whatsapp")}
            {renderSocialLinks(data?.Others?.slice(0, 2), "others")}
          </div>
        </div>

        <div className={styles.readmorebuttonmaindiv}>
          <div className={styles.readmorebuttonsubdiv}></div>
        </div>
        <div className={styles.footer}>
          <span className={styles.headerText}>OSINT</span>
        </div>
        {shouldDisplayReadMore && (
          <span onClick={handleReadMore} className={styles.readmorebutton}>
            Read More...
          </span>
        )}
      </Panel>

      {/* Modal to show complete details */}
       
      <Modal
        open={modalOpen}
        onClose={handleCloseModal}
        className={styles.MainModalStyling}
        backdrop="static"
      >
        <CloseIcon
          onClick={() => handleCloseModal()}
          className={styles.clear}
        />
        <Modal.Body className={styles.modalData}>
          <Panel bordered className={styles.modalThreatCard}>
            <div className={styles.modalHeader}>
              <div className={styles.modalImageDiv}>
                <img
                  src="/static/images/IJhNWg.jpg"
                  alt="Profile"
                  width="100%"
                  height="150"
                  className={styles.bg_card_Image}
                />
              </div>
              <div className={styles.parentmodalProfileImage}>
                <div className={styles.modalProfileImage}>
                  {/* {data?.Image &&
                    data?.Image?.$binary &&
                    data?.Image?.$binary?.base64 && (
                      <img
                        src={`data:image/jpeg;base64,${data?.Image?.$binary?.base64}`}
                        alt="Profile"
                        className={styles.Modal_card_Image}
                      />
                    )} */}
                     {renderImage()}
                </div>
              </div>
              <div className={styles.userName}>{data?.Name[0]}</div>
            </div>
          </Panel>
          <div className={styles.modalContactDetails}>
            <table className={styles.table}>
               <tbody>
        {Object.entries(data)?.map(([key, value], index) => {
          const lowercaseKey = key?.toLowerCase();
          const selectedIcon = keyIconMapping[lowercaseKey];

          if (!value || (Array?.isArray(value) && value?.every(v => !v))) {
            return null; // Skip rendering if there is no data
          }

          return (
            index < displayKeysInModal &&
            key !== "Image" && (
              <tr key={key}>
                <td>
                  {Array?.isArray(value) ? (
                    value
                      ?.filter(link => link?.trim() !== "") // Filter out empty links
                      ?.map((link, linkIndex) => (
                        <div
                          key={linkIndex}
                          className={styles.modalValueData}
                        >
                          {selectedIcon && (
                            <FontAwesomeIcon
                              icon={selectedIcon}
                              className={styles.modalfontIconStyling}
                            />
                          )}
                          <span className={styles.modalCoolon}>:</span>
                          {isValidUrl(link) ? (
                            <a
                              href={link}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              {link}
                            </a>
                          ) : (
                            link
                          )}
                        </div>
                      ))
                  ) : (
                    <div className={styles.modalValueData}>
                      {selectedIcon && (
                        <FontAwesomeIcon
                          icon={selectedIcon}
                          className={styles.modalfontIconStyling}
                        />
                      )}
                      <span className={styles.modalCoolon}>:</span>
                      {isValidUrl(value) ? (
                        <a
                          href={value}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          {value}
                        </a>
                      ) : (
                        value
                      )}
                    </div>
                  )}
                </td>
              </tr>
            )
          );
        })}
      </tbody>
            </table>
          </div>
        </Modal.Body>

        <Modal.Footer></Modal.Footer>
      </Modal>
    </>
  );
};

export default ThreatCard;
